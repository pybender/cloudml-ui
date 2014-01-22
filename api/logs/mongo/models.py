from datetime import datetime
from flask.ext.mongokit import Document

from api import app


@app.conn.register
class LogMessage(Document):
    TRAIN_MODEL = 'trainmodel_log'
    IMPORT_DATA = 'importdata_log'
    RUN_TEST = 'runtest_log'
    CONFUSION_MATRIX_LOG = 'confusion_matrix_log'
    TYPE_CHOICES = (TRAIN_MODEL, IMPORT_DATA, RUN_TEST,
                    CONFUSION_MATRIX_LOG)

    __collection__ = 'logs'
    structure = {
        # error, warning
        'level': basestring,
        # operation type: run test, train model, etc
        'type': basestring,
        'params': dict,
        'content': basestring,
        'created_on': datetime,
    }
    default_values = {'created_on': datetime.utcnow}
    use_dot_notation = True

    @classmethod
    def delete_related_logs(cls, obj, level=None):
        # TODO: implement level
        app.db.LogMessage.collection.remove({'params.obj': int(obj.id),
                                             'type': obj.LOG_TYPE})
