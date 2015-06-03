# Authors: Nikolay Melnik <nmelnik@upwork.com>

import time
from datetime import datetime, timedelta
import logging
import uuid

from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
from boto.dynamodb2.types import NUMBER, STRING
from boto.exception import JSONResponseError

from api.amazon_utils import AmazonDynamoDBHelper


db = AmazonDynamoDBHelper()


class LogMessage(object):
    TRAIN_MODEL = 'trainmodel_log'
    IMPORT_DATA = 'importdata_log'
    RUN_TEST = 'runtest_log'
    CONFUSION_MATRIX_LOG = 'confusion_matrix_log'
    TYPES_LIST = (TRAIN_MODEL, IMPORT_DATA, RUN_TEST,
                  CONFUSION_MATRIX_LOG)
    LEVELS_LIST = ['CRITICAL', 'ERROR', 'WARN', 'WARNING',
                   'INFO', 'DEBUG', 'NOTSET']

    TABLE_NAME = 'cloudml-log'

    # TODO: add indexes (by level etc.)
    SCHEMA = [
        HashKey('object_id', data_type=NUMBER),
        RangeKey('id', data_type=STRING)
    ]

    def __init__(self, type_, content, object_id=None, level='INFO'):
        self.id = '{0}:{1}'.format(type_, str(time.time()))
        self.type = type_
        self.content = content
        self.object_id = object_id
        self.level = level
        self.created_on = time.time()

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'object_id': self.object_id,
            'level': self.LEVELS_LIST.index(self.level),
            'created_on': self.created_on
        }

    def save(self):
        data = self.to_dict()
        db.put_item(self.TABLE_NAME, data)

    @classmethod
    def create_table(cls):
        db.create_table(cls.TABLE_NAME, cls.SCHEMA)

    @classmethod
    def filter_by_object(cls, log_type, object_id, next_token, order_str,
                         level=None, limit=None):
        query_filter = {}
        params = {
            'object_id__eq': object_id,
            'id__beginswith': log_type
        }

        order_asc = True if order_str == 'asc' else False
        try:
            next_token = float(next_token)
        except (ValueError, TypeError):
            next_token = None

        if order_asc:
            next_token = next_token if next_token is not None else 0
            query_filter['created_on__gt'] = next_token
        else:
            day_ahead = datetime.now() + timedelta(1)
            next_token = next_token if next_token is not None else \
                time.mktime(day_ahead.timetuple())
            query_filter['created_on__lt'] = next_token

        if level is not None and level in cls.LEVELS_LIST:
            idx = cls.LEVELS_LIST.index(level)
            query_filter['level__lte'] = idx

        items = []
        res = db.get_items(cls.TABLE_NAME, limit=limit, reverse=not order_asc,
                           query_filter=query_filter, **params)
        new_next_token = None
        for item in res:
            try:
                new_next_token = item['created_on']
                item['created_on'] = datetime.fromtimestamp(item['created_on'])
                item['level'] = cls.LEVELS_LIST[int(item['level'])]
            except TypeError:
                pass
            items.append(item)
        new_next_token = None if len(items) < limit else new_next_token
        return items, new_next_token

    @classmethod
    def delete_related_logs(cls, object_id, level=None):
        from api import app
        if not app.config['TEST_MODE']:
            db.delete_items(cls.TABLE_NAME, object_id__eq=object_id)
