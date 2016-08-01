# Authors: Nikolay Melnik <nmelnik@upwork.com>

import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import logging
from boto3.dynamodb.conditions import Key, Attr
from api.amazon_utils import AmazonDynamoDBHelper


db = AmazonDynamoDBHelper()


class LogMessage(object):
    TRAIN_MODEL = 'trainmodel_log'
    IMPORT_DATA = 'importdata_log'
    RUN_TEST = 'runtest_log'
    VERIFY_MODEL = 'verifymodel_log'
    CONFUSION_MATRIX_LOG = 'confusion_matrix_log'
    TRAIN_TRANSFORMER = 'traintransformer_log'
    GRID_SEARCH = 'gridsearch_log'
    TYPES_LIST = (TRAIN_MODEL, IMPORT_DATA, RUN_TEST,
                  CONFUSION_MATRIX_LOG, VERIFY_MODEL,
                  TRAIN_TRANSFORMER, GRID_SEARCH)
    LEVELS_LIST = ['CRITICAL', 'ERROR', 'WARN', 'WARNING',
                   'INFO', 'DEBUG', 'NOTSET']

    TABLE_NAME = 'cloudml-log'

    # TODO: add indexes (by level etc.)
    SCHEMA = [{'AttributeName': 'object_id', 'KeyType': 'HASH'},
              {'AttributeName': 'id', 'KeyType': 'RANGE'}]

    SCHEMA_TYPES = [{'AttributeName': 'object_id', 'AttributeType': 'N'},
                    {'AttributeName': 'id', 'AttributeType': 'S'}]

    def __init__(self, type_, content, object_id=None, level='INFO'):
        self.id = '{0}:{1}'.format(type_, str(time.time()))
        self.type = type_
        self.content = content
        self.object_id = object_id
        self.level = level
        self.created_on = self._to_decimal(time.time())

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'object_id': self.object_id,
            'level': self.LEVELS_LIST.index(self.level),
            'created_on': self._to_decimal(self.created_on)
        }

    @classmethod
    def _to_decimal(cls, value):
        return Decimal(str(value)).quantize(Decimal('0.01'),
                                            rounding=ROUND_DOWN)

    def save(self):
        data = self.to_dict()
        db.put_item(self.TABLE_NAME, data)

    @classmethod
    def create_table(cls):
        db.create_table(cls.TABLE_NAME, cls.SCHEMA, cls.SCHEMA_TYPES)

    @classmethod
    def filter_by_object(cls, log_type, object_id, next_token, order_str,
                         level=None, limit=None):
        key_condition_expression = Key('object_id').eq(object_id)

        order_asc = True if order_str == 'asc' else False
        try:
            next_token = float(next_token)
        except (ValueError, TypeError):
            next_token = None

        if order_asc:
            next_token = next_token if next_token is not None else 0
            key_condition_expression = key_condition_expression & \
                Key('id').gt(log_type+":"+str(next_token))
        else:
            day_ahead = datetime.now() + timedelta(1)
            next_token = next_token if next_token is not None else \
                time.mktime(day_ahead.timetuple())
            key_condition_expression = key_condition_expression & \
                Key('id').lt(log_type+":"+str(next_token))

        query_params = {'KeyConditionExpression': key_condition_expression,
                        'ScanIndexForward': order_asc,
                        'FilterExpression': Attr('type').eq(log_type)}
        if limit is not None:
            query_params['Limit'] = limit

        if level is not None and level in cls.LEVELS_LIST:
            idx = cls.LEVELS_LIST.index(level)
            query_params['FilterExpression'] = \
                query_params['FilterExpression'] & Attr('level').lte(idx)

        items = []
        res = db.get_items(cls.TABLE_NAME, **query_params)

        new_next_token = None
        for item in res:
            try:
                new_next_token = item['created_on']
                item['created_on'] = datetime.fromtimestamp(
                    float(item['created_on']))
                item['level'] = cls.LEVELS_LIST[int(item['level'])]
            except TypeError:
                pass
            items.append(item)
        new_next_token = None if len(items) < limit else new_next_token
        return items, new_next_token

    @classmethod
    def delete_related_logs(cls, object_id, level=None, type_=TRAIN_MODEL):
        from api import app
        if not app.config['TEST_MODE']:
            db.delete_items(
                cls.TABLE_NAME, keys=['id', 'object_id'],
                KeyConditionExpression=Key('object_id').eq(object_id) &
                Key('id').begins_with(type_))
