# Authors: Nikolay Melnik <nmelnik@upwork.com>

import celery

from api import app
from api.base.exceptions import ApiBaseException
import json


db_session = app.sql_db.session


def get_task_traceback(exc):
    e = TaskException(exc.message, exc)
    if e.traceback:
        return json.dumps(e.traceback)
    return ''


class TaskException(ApiBaseException):
      pass


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True
