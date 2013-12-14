from celery.signals import task_prerun, task_postrun

from api import celery
from api.async_tasks.models import AsyncTask
from api.import_handlers.models import DataSet
from api.ml_models.models import Model
from api.model_tests.models import TestResult


def get_object_from_task(task, args, kwargs):  # pragma: no cover
    cls = None
    obj_id = None
    if task.name == 'api.import_handlers.tasks.import_data':
        cls = DataSet
        obj_id = args[0] if len(args) else kwargs['dataset_id']
    elif task.name == 'api.model_tests.tasks.run_test':
        cls = TestResult
        obj_id = args[1] if len(args) else kwargs['test_id']
    elif task.name in ('api.ml_models.tasks.train_model',
                       'api.ml_models.tasks.fill_model_parameter_weights'):
        cls = Model
        if task.name == 'api.ml_models.tasks.train_model':
            obj_id = args[1] if len(args) else kwargs['model_id']
        elif task.name == 'api.ml_models.tasks.fill_model_parameter_weights':
            obj_id = args[0] if len(args) else kwargs['model_id']
    elif task.name == 'api.model_tests.tasks.get_csv_results':
        cls = TestResult
        obj_id = args[1] if len(args) else kwargs['test_id']
    elif task.name == 'api.model_tests.tasks.calculate_confusion_matrix':
        cls = TestResult
        obj_id = args[0] if len(args) else kwargs['test_id']

    return cls.query.filter_by(id=int(obj_id)).first() \
        if cls and obj_id \
        else None


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None,
                        kwargs=None, **kwds):  # pragma: no cover
    obj = get_object_from_task(task, args, kwargs)
    if obj:
        task_obj = AsyncTask.create_by_task_and_object(task.name, task_id, obj)
        task_obj.save()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None,
                         kwargs=None, retval=None, state=None,
                         **kwds):  # pragma: no cover
    task_obj = AsyncTask.query.filter_by(task_id=task_id).first()
    if task_obj:
        if isinstance(retval, Exception):
            task_obj.status = AsyncTask.STATUS_ERROR
            task_obj.error = str(retval)
        else:
            task_obj.status = AsyncTask.STATUS_COMPLETED
            task_obj.result = retval
        task_obj.save()
