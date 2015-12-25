# Authors: Nikolay Melnik <nmelnik@upwork.com>

import celery

from api import app
from cloudml import ChainedException, traceback_info

db_session = app.sql_db.session


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True


def get_task_traceback(exc):
    if isinstance(exc, ChainedException):
        traceback = exc.traceback
    else:
        traceback = traceback_info()
    return traceback


class CloudmlUITaskException(ChainedException):
    pass