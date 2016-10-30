from api import celery, app
from api.base.tasks import UnwrapArgs, wrapchain
from celery.utils.log import get_logger
from api.logs.logger import init_logger

@celery.task()
@wrapchain
def scenarios_task_loger(*args, **kwargs):
    scenarios_task_loger_arg = {}
    if 'scenarios_task_loger_arg' in kwargs:
        scenarios_task_loger_arg = kwargs.get('scenarios_task_loger_arg', {})
        del kwargs['scenarios_task_loger_arg']
    id = scenarios_task_loger_arg.get('scenariosid', 0)
    logger = init_logger('trainmodel_log', obj=int(id))
    scenarios = scenarios_task_loger_arg.get('scenarios', 'Scenario.')
    chainname = scenarios_task_loger_arg.get('chainname', 'Chainname.')
    name = scenarios_task_loger_arg.get('name', 'funct')
    text = scenarios_task_loger_arg.get('text', '...')
    logger.info("Scenarios: {0}; Chain: {1}; Task in chain: {2}; Info: {3}.".format(scenarios, chainname, name, text))
    return UnwrapArgs((args, kwargs))