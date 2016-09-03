# Authors: Nikolay Melnik <nmelnik@upwork.com>

import celery

from api import app
from api.base.exceptions import ApiBaseException
from cloudml.exceptions import print_exception


db_session = app.sql_db.session


def get_task_traceback(exc):
    return print_exception(exc, with_colors=False, ret_value=True)


class TaskException(ApiBaseException):
      pass


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True
