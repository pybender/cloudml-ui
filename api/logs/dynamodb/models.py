import time
import datetime
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
        uid = str(uuid.uuid1().hex)
        self.id = '{0}:{1}:{2}'.format(type_, str(time.time()), uid)
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
        try:
            Table.create(cls.TABLE_NAME, connection=db.conn,
                         schema=cls.SCHEMA)
        except JSONResponseError as ex:
            logging.exception(str(ex))

    @classmethod
    def filter_by_object(cls, log_type, object_id,
                         level=None, limit=None, next_token=None):
        params = {
            'object_id__eq': object_id,
            'id__beginswith': log_type
        }

        if level is not None and level in cls.LEVELS_LIST:
            idx = cls.LEVELS_LIST.index(level)
            params['level__lte'] = idx

        items = []
        res, next_token = db.get_items(
            cls.TABLE_NAME,
            limit=limit,
            next_token=next_token,
            reverse=False,
            **params
        )
        for item in res:
            try:
                item['created_on'] = datetime.datetime.fromtimestamp(
                    item['created_on'])
                item['level'] = cls.LEVELS_LIST[int(item['level'])]
            except TypeError:
                pass
            items.append(item)
        return items, next_token

    @classmethod
    def delete_related_logs(cls, object_id, level=None):
        from api import app
        if not app.config['TEST_MODE']:
            db.delete_items(cls.TABLE_NAME, object_id=object_id)
