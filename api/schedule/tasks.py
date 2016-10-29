import time
import functools
from celery import current_task
from celery.utils.log import get_logger, get_task_logger

from api import celery, app
from api.base.tasks import SqlAlchemyTask
from api.schedule.models import PeriodicTaskScenarios

logger = get_logger(__name__)

class UnwrapArgs(object):
    def __init__(self, contents):
        self.contents = contents

    def __call__(self):
        return self.contents

def wrapchain(f):
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        if type(args[0]) == UnwrapArgs:
            inargs = list(args[0]())
            lastargs = args[1:]
            args = []
            for a in inargs:
                if isinstance(a, dict):
                    kwargs.update(a)
                elif isinstance(a, (list, tuple)):
                    args.extend(a)
                else:
                    args.append(a)
            args = list(args) + list(lastargs)
        result = f(*args, **kwargs)
        if type(result) == tuple and current_task.request.callbacks:
            return UnwrapArgs(result)
        else:
            return result
    return _wrapper

@celery.task()
@wrapchain
def scenarios_task_loger(*args, **kwargs):
    scenarios_task_loger_arg = {}
    if 'scenarios_task_loger_arg' in kwargs:
        scenarios_task_loger_arg = kwargs.get('scenarios_task_loger_arg', {})
        del kwargs['scenarios_task_loger_arg']
    scenarios = scenarios_task_loger_arg.get('scenarios', 'Scenario.')
    chainname = scenarios_task_loger_arg.get('chainname', 'Chainname.')
    name = scenarios_task_loger_arg.get('name', 'funct')
    text = scenarios_task_loger_arg.get('text', '...')
    logger.error("Scenarios: {0} Chain: {1} Task in chain: {2} Info: {3}".format(scenarios, chainname, name, text))
    return UnwrapArgs((args, kwargs))

@celery.task(base=SqlAlchemyTask)
@wrapchain
def test_task(*args, **kwargs):
    name = kwargs.get('name', 'None')
    time.sleep(15)
    print("single:", args, kwargs)
    return name

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
        logger.info('Task end.')
        return 'Completed.'
    except Exception as e:
        logger.error('Error error processing scenarios task (%s).' % e)
        return 'Error.'

