import uuid
from datetime import datetime

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

    def __init__(self, type_, content, object_id=None, level='INFO'):
        self.id = str(uuid.uuid1())
        self.type = type_
        self.content = content
        self.object_id = object_id
        self.level = level
        self.created_on = datetime.now()

    def to_dict(self):
        return {'type': self.type,
                'content': self.content,
                'object_id': self.object_id,
                'level': self.level,
                'created_on': str(self.created_on)} # TODO: str

    def save(self):
        db.put_item('logs', self.to_dict())

    @classmethod
    def filter_by_object(cls, log_type, object_id,
                         level=None, limit=None, next_token=None):
        params = {
            'type__eq': log_type,
            'object_id__eq': object_id,
        }
        if level is not None:
            idx = cls.LEVELS_LIST.index(level)
            levels = ["'%s'" % l for i, l in enumerate(cls.LEVELS_LIST)
                      if i <= idx]
            params['level__in'] = levels

        return db.get_items('logs', params, limit=limit)
