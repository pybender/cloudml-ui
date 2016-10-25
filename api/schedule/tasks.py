from api import celery, app
from api.base.tasks import SqlAlchemyTask
from celery.utils.log import get_logger, get_task_logger
from api.schedule.models import PeriodicTaskScenarios
import time
logger = get_logger(__name__)

@celery.task(base=SqlAlchemyTask)
def test_task_01(*args, **kwargs):
    name = kwargs.get('name', 'None')
    time.sleep(15)
    print("single:", args, kwargs)
    return name

@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def test_schedule_task():
    tasklog = get_task_logger(__name__)
    tasklog.debug('Start...')
    for i in range(0, 1000000):
        k = i * i
    logger.debug('Test %s completed.' % 'test_schedule_task')
    return 'test_schedule_task completed'

@celery.task(base=SqlAlchemyTask)
def scenarios_task_loger(*args, **kwargs):

    return args, kwargs

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
            result = task.sctasks.delay()
            # result = result.get()
            # while not result.ready(): print ("wait result") time.sleep(2)
        logger.info('Task end.')
        return 'Completed'
    except Exception as e:
        logger.error('Error error processing scenarios task (%s).' % e)
        return 'Error.ProcessingTask'

