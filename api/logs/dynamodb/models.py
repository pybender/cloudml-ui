import time
import datetime

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

    TABLE_NAME = 'logs'

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
            'level': self.level,
            'created_on': self.created_on
        }

    def save(self):
        data = self.to_dict()
        db.put_item(LogMessage.TABLE_NAME, data)

    @classmethod
    def filter_by_object(cls, log_type, object_id,
                         level=None, limit=None, next_token=None):
        params = {
            'object_id__eq': object_id,
            'id__beginswith': log_type
        }

        # TODO: it is not possible to filter by list without full table scan
        if level is not None:
            idx = cls.LEVELS_LIST.index(level)
            levels = ["'%s'" % l for i, l in enumerate(cls.LEVELS_LIST)
                      if i <= idx]
            params['level__in'] = levels

        items = []
        res, next_token = db.get_items(
            LogMessage.TABLE_NAME,
            limit=limit,
            next_token=next_token,
            reverse=False,
            **params
        )
        for item in res:
            try:
                item['created_on'] = datetime.datetime.fromtimestamp(
                    item['created_on'])
            except TypeError:
                pass
            items.append(item)
        return items, next_token

    @classmethod
    def delete_related_logs(cls, obj, level=None):
        db.delete_items(LogMessage.TABLE_NAME, object_id__eq=obj.id)


# TODO: refactor
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
from boto.dynamodb2.types import NUMBER, STRING
from boto.exception import JSONResponseError
if not db._tables.get(LogMessage.TABLE_NAME):
    schema = [
        HashKey('object_id', data_type=NUMBER),
        RangeKey('id', data_type=STRING)
    ]
    try:
        Table.create(LogMessage.TABLE_NAME, connection=db.conn, schema=schema)
    except JSONResponseError as ex:
        print str(ex)
