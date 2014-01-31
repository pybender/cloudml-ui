import uuid
from datetime import datetime

from amazon_utils import AmazonDynamoDBHelper


ddb = AmazonDynamoDBHelper()


class LogMessage(object):
    TRAIN_MODEL = 'trainmodel_log'
    IMPORT_DATA = 'importdata_log'
    RUN_TEST = 'runtest_log'
    CONFUSION_MATRIX_LOG = 'confusion_matrix_log'
    TYPES_LIST = (TRAIN_MODEL, IMPORT_DATA, RUN_TEST,
                  CONFUSION_MATRIX_LOG)
    LEVELS_DICT = ['CRITICAL', 'ERROR', 'WARN', 'WARNING',
                   'INFO', 'DEBUG', 'NOTSET']

    def __init__(self, type_, content, object_id=None, level='INFO'):
        self.id = str(uuid.uuid1())
        self.type = type_
        self.content = content
        self.object_id = object_id
        self.level = level
        self.created_on = datetime.now()
        self.is_sync = False

    def to_dict(self):
        return {'content': self.content,
                'object_id': self.object_id,
                'level': self.level,
                'created_on': self.created_on}

    def save(self):
        sdb.put_item(self.type, self.id, self.to_dict())
        self.is_sync = True

    @classmethod
    def filter_by_object(self, log_type, object_id,
                         level=None, limit=None, next_token=None):
        filter_str = 'object_id = %s and created_on > 2014' % object_id
        if level is not None:
            idx = self.LEVELS_LIST.index(level)
            levels = ["'%s'" % l for i, l in enumerate(self.LEVELS_LIST) if i <= idx]
            filter_str += ' and level in (%s)' % ','.join(levels)
        order_by = 'created_on desc'
        return sdb.get_items(
            log_type, filter_str=filter_str, order_by=order_by,
            limit=limit, next_token=next_token)
