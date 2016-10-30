import time
import functools
from celery import current_task
from celery.utils.log import get_logger, get_task_logger

from api import celery, app
from api.base.tasks import SqlAlchemyTask, UnwrapArgs, wrapchain
from api.schedule.models import PeriodicTaskScenarios

logger = get_logger(__name__)

@celery.task(base=SqlAlchemyTask)
@wrapchain
def test_task(*args, **kwargs):
    name = kwargs.get('name', 'None')
    print("single:", args, kwargs)
    time.sleep(5)
    return name, {'res': 100, 'nameout': name}

@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def scenarios_schedule_task(*args, **kwargs):
    try:
        taskid = kwargs.get('scenario_task_id', None)
        if not taskid:
            raise ValueError('Error get scenarios task  id: %s .' % taskid)
        taskid = int(taskid)
        logger.info('Task %s start...' % taskid)
        task = PeriodicTaskScenarios.query.filter_by(id=taskid).first()
        if not task:
            raise ValueError('Error get scenarios task  id: %s from db.' % taskid)
        if task.task_parser():
            logger.info('Start task %s .' % task.name)
            #result = task.sctasks.delay(serializer='pickle')
            result = task.sctasks.apply_async(serializer='pickle')

        logger.info('Task end.')
        return 'Completed.'
    except Exception as e:
        logger.error('Error error processing scenarios task (%s).' % e)
        return 'Error.'

