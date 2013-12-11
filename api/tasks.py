from celery.signals import task_prerun, task_postrun

from api import celery


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None,
                        kwargs=None, **kwds):  # pragma: no cover
    cls = None
    obj_id = None
    if task.name == 'api.tasks.import_data':
        cls = app.db.DataSet
        obj_id = args[0] if len(args) else kwargs['dataset_id']
    elif task.name == 'api.tasks.run_test':
        cls = app.db.Test
        obj_id = args[1] if len(args) else kwargs['test_id']
    elif task.name in ('api.tasks.train_model',
                       'api.tasks.fill_model_parameter_weights'):
        cls = app.db.Model
        if task.name == 'api.tasks.train_model':
            obj_id = args[1] if len(args) else kwargs['model_id']
        elif task.name == 'api.tasks.fill_model_parameter_weights':
            obj_id = args[0] if len(args) else kwargs['model_id']

    # TODO
    # if cls and obj_id:
    #     obj = cls.get_from_id(ObjectId(obj_id))
    #     if obj:
    #         obj.current_task_id = task_id
    #         obj.save()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None,
                         kwargs=None, retval=None, state=None,
                         **kwds):  # pragma: no cover
    cls = None
    if task.name == 'api.tasks.import_data':
        cls = app.db.DataSet
    elif task.name == 'api.tasks.run_test':
        cls = app.db.Test
    elif task.name in ('api.tasks.train_model',
                       'api.tasks.fill_model_parameter_weights'):
        cls = app.db.Model

    # TODO
    # if cls:
    #     cls.collection.update(
    #         {'current_task_id': task_id}, {'$set': {'current_task_id': ''}},
    #         multi=True
    #     )
