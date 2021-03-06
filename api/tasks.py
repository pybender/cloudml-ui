from celery.signals import task_prerun, task_postrun, task_sent

from api import celery
from api.async_tasks.models import AsyncTask
from api.import_handlers.models import DataSet, XmlSqoop
from api.ml_models.models import Model, Segment
from api.model_tests.models import TestResult
from api.instances.models import Cluster

IMPORT_DATA = 'api.import_handlers.tasks.import_data'
TRAIN_MODEL_TASK = 'api.ml_models.tasks.models.train_model'
TRANSFORM_DATASET_TASK = 'api.ml_models.tasks.models.\
transform_dataset_for_download'
VISUALIZE_MODEL_TASK = 'api.ml_models.tasks.models.visualize_model'
TRAIN_TRANSFORMER = 'api.ml_models.tasks.transformers.train_transformer'
TRANSFORMERS_UPLOAD_TASK = 'api.ml_models.tasks.models.' \
                           'upload_segment_features_transformers'


def get_object_from_task(task_name, args, kwargs):  # pragma: no cover
    cls = None
    obj_id = None
    if task_name == 'api.import_handlers.tasks.import_data':
        cls = DataSet
        obj_id = args[0] if len(args) else kwargs['dataset_id']
    elif task_name == 'api.model_tests.tasks.run_test':
        cls = TestResult
        obj_id = args[1] if len(args) else kwargs['test_id']
    elif task_name in (TRAIN_MODEL_TASK, VISUALIZE_MODEL_TASK,
                       TRANSFORM_DATASET_TASK):
        cls = Model
        if task_name == TRAIN_MODEL_TASK:
            obj_id = args[1] if len(args) > 1 else kwargs['model_id']
        elif task_name == VISUALIZE_MODEL_TASK:
            obj_id = args[0] if len(args) else kwargs['model_id']
        elif task_name == TRANSFORM_DATASET_TASK:
            obj_id = args[0] if len(args) else kwargs['model_id']
    elif task_name == 'api.model_tests.tasks.get_csv_results':
        cls = TestResult
        obj_id = args[1] if len(args) else kwargs['test_id']
    elif task_name == 'api.model_tests.tasks.export_results_to_db':
        cls = TestResult
        obj_id = args[1] if len(args) else kwargs['test_id']
    elif task_name == 'api.model_tests.tasks.calculate_confusion_matrix':
        cls = TestResult
        obj_id = args[0] if len(args) else kwargs['test_id']
    elif task_name == 'api.instances.tasks.run_ssh_tunnel':
        cls = Cluster
        obj_id = args[0] if len(args) else kwargs['cluster_id']
    elif task_name == 'api.import_handlers.tasks.load_pig_fields':
        cls = XmlSqoop
        obj_id = args[0] if len(args) else kwargs['sqoop_id']
    elif task_name == TRANSFORMERS_UPLOAD_TASK:
        cls = Segment
        obj_id = args[1] if len(args) else kwargs['segment_id']

    return cls.query.filter_by(id=int(obj_id)).first() \
        if cls and obj_id \
        else None


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None,
                        kwargs=None, **kwds):  # pragma: no cover
    obj = get_object_from_task(task.name, args, kwargs)
    if obj:
        task_obj = AsyncTask.create_by_task_and_object(
            task.name,
            task_id,
            args,
            kwargs,
            obj)
        task_obj.save()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None,
                         kwargs=None, retval=None, state=None,
                         **kwds):  # pragma: no cover
    task_obj = AsyncTask.query.filter_by(task_id=task_id).first()
    if task_obj:
        if isinstance(retval, Exception):
            task_obj.status = AsyncTask.STATUS_ERROR
            task_obj.error = str(retval)[0:299]
        else:
            task_obj.status = AsyncTask.STATUS_COMPLETED
            task_obj.result = retval
        task_obj.save()
