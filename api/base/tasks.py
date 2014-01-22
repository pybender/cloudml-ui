import celery

from api import app

db_session = app.sql_db.session


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     db_session.remove()
