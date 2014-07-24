import logging

from sqlalchemy import desc
from flask.ext.sqlalchemy import before_models_committed

from api.base.models import db, BaseModel, JSONType


class AsyncTask(db.Model, BaseModel):
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_COMPLETED = 'Completed'
    STATUS_ERROR = 'Error'

    STATUSES = [STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_ERROR]

    status = db.Column(db.Enum(*STATUSES, name='async_task_statuses'),
                       default=STATUS_IN_PROGRESS)
    error = db.Column(db.String(300))
    args = db.Column(JSONType)
    kwargs = db.Column(JSONType)
    result = db.Column(JSONType)

    task_name = db.Column(db.String(300))
    task_id = db.Column(db.String(300))

    object_type = db.Column(db.String(300))
    object_id = db.Column(db.Integer)

    @classmethod
    def _get_object_type_name(cls, obj):
        return obj.__class__.__name__

    @classmethod
    def create_by_task_and_object(cls, task_name, task_id, args, kwargs, obj):
        return cls(
            task_name=task_name,
            task_id=task_id,
            object_type=cls._get_object_type_name(obj),
            object_id=obj.id,
            args=args,
            kwargs=kwargs
        )

    @classmethod
    def get_current_by_object(cls, obj, task_name=None, user=None, **kwargs):
        cursor = cls.query.filter_by(
            object_type=cls._get_object_type_name(obj),
            object_id=obj.id,
        ).filter(
            cls.status.in_([cls.STATUS_IN_PROGRESS, cls.STATUS_COMPLETED])
        )
        if task_name:
            cursor = cursor.filter_by(task_name=task_name)
        if user:
            cursor = cursor.filter_by(created_by=user)
        if kwargs:
            cursor = cursor.filter_by(**kwargs)
        return cursor.order_by(desc(AsyncTask.created_on)).all()

    def terminate_task(self):
        from api import celery
        # try:
        

        # import signal

        # def kill_child_processes(parent_pid, sig=signal.SIGKILL, top=True):
        #     ps_command = subprocess.Popen("ps -o pid --ppid %d --noheaders" % parent_pid, shell=True, stdout=subprocess.PIPE)
        #     ps_output = ps_command.stdout.read()
        #     retcode = ps_command.wait()
        #     if retcode != 0: return
        #     for pid_str in ps_output.split("n")[:-1]:
        #         try:
        #             kill_child_processes(int(pid_str), sig, top=False)

        #             if not top: os.kill(int(pid_str), sig)
        #         except OSError: pass

        # kill_child_processes()

        celery.control.revoke(self.task_id, terminate=True, signal='SIGKILL')

        # except Exception as e:
        #     logging.exception(e)


@before_models_committed.connect
def on_before_models_committed(sender, changes):
    """
    Signal handler to stop all running tasks related to object
    that is being deleted.
    :param sender:
    :param changes:
    :return:
    """
    MODELS_TO_TRACK = ['DataSet', 'Model', 'TestResult']
    dels = [obj for obj, oper in changes
            if oper == 'delete' and obj.__class__.__name__ in MODELS_TO_TRACK]
    for obj in dels:
        for task in AsyncTask.get_current_by_object(obj):
            task.terminate_task()
