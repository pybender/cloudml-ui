import logging

from sqlalchemy import desc

from api.base.models import db, BaseModel, JSONType


class AsyncTask(db.Model, BaseModel):
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_COMPLETED = 'Completed'
    STATUS_ERROR = 'Error'

    STATUSES = [STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_ERROR]

    status = db.Column(db.Enum(*STATUSES, name='async_task_statuses'),
                       default=STATUS_IN_PROGRESS)
    error = db.Column(db.String(300))
    result = db.Column(JSONType)

    task_name = db.Column(db.String(300))
    task_id = db.Column(db.String(300))

    object_type = db.Column(db.String(300))
    object_id = db.Column(db.Integer)

    @classmethod
    def _get_object_type_name(cls, obj):
        return obj.__class__.__name__

    @classmethod
    def create_by_task_and_object(cls, task_name, task_id, obj):
        return cls(
            task_name=task_name,
            task_id=task_id,
            object_type=cls._get_object_type_name(obj),
            object_id=obj.id,
        )

    @classmethod
    def get_current_by_object(cls, task_name, obj, user=None):
        cursor = cls.query.filter_by(
            task_name=task_name,
            object_type=cls._get_object_type_name(obj),
            object_id=obj.id,
            status=cls.STATUS_IN_PROGRESS,
        )
        if user:
            cursor = cursor.filter_by(created_by=user)
        return cursor.order_by(desc(AsyncTask.created_on)).all()

    def terminate_task(self):
        from api import celery
        try:
            celery.control.revoke(self.task_id, terminate=True)
        except Exception as e:
            logging.exception(e)
