import uuid
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
        uid = str(uuid.uuid1())
        self.id = '{0}:{1}'.format(type_, uid)
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
            reverse=True,
            **params
        )
        for item in res:
            item['created_on'] = datetime.datetime.fromtimestamp(
                item['created_on'])
            items.append(item)
        return items, next_token

    @classmethod
    def delete_related_logs(cls, obj, level=None):
        # TODO: implement
        pass
