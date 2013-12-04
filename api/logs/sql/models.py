from sqlalchemy.orm import deferred
from sqlalchemy import Integer, String, Enum
from sqlalchemy import func

from api.base.models import BaseMixin, db
from api.db import JSONType


class LogMessage(BaseMixin, db.Model):
    TRAIN_MODEL = 'trainmodel_log'
    IMPORT_DATA = 'importdata_log'
    RUN_TEST = 'runtest_log'
    CONFUSION_MATRIX_LOG = 'confusion_matrix_log'
    TYPES_LIST = (TRAIN_MODEL, IMPORT_DATA, RUN_TEST,
                  CONFUSION_MATRIX_LOG)
    LEVELS_LIST = ['CRITICAL', 'ERROR', 'WARN', 'WARNING',
                   'INFO', 'DEBUG', 'NOTSET']

    id = db.Column(Integer, primary_key=True)
    level = db.Column(Enum(*LEVELS_LIST, name='log_levels'))
    params = deferred(db.Column(JSONType))
    content = deferred(db.Column(String(600)))
    type = db.Column(Enum(*TYPES_LIST, name='log_types'))
    created_on = db.Column(db.DateTime, server_default=func.now())

    @classmethod
    def delete_related_logs(cls, obj):
        # TODO: fill with code
        pass
