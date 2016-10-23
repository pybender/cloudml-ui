import celery
#from celery.task.control import revoke
from api import celery as app
from celery.utils.log import get_logger
from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history

from .base import Base, Session
from .models import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule, PeriodicTaskScenarios)

__all__ = [
    'Base',
    'PeriodicTask',
    'CrontabSchedule',
    'PeriodicTasks',
    'IntervalSchedule',
    'PeriodicTaskScenarios',
    'Session'
]
logger = get_logger(__name__)

class ConstraintError(Exception):
    pass

def before_update_periodic_task(mapper, connection, target):
    try:
        old_name = get_history(target, 'name')[2][0]
        new_name = get_history(target, 'name')[0][0]
        if old_name != new_name:
            if target.task == 'api.schedule.tasks.scenarios_schedule_task':
                raise ConstraintError('Cannot change scenarios schedule task name.')
    except:
        pass
        #logger.error("Can't get_history for PeriodicTask attribute 'name' in before_update_periodic_task func.")

def after_update(mapper, connection, target):
    session = Session()

    if not target.interval and not target.crontab:
        raise ConstraintError('One of interval or crontab must be set.')
    if target.interval and target.crontab:
        raise ConstraintError('Only one of interval or crontab must be set')

    PeriodicTasks.changed(session, target)
# TODO correct delete beat task fro celery

def after_delete_periodic_task_scenarios(mapper, connection, target):
    session = Session()
    try:
        task = PeriodicTask.filter_by(session, id=target.periodictask_id).first()
        if task:
            session.delete(task)
            session.flush()
    except Exception as e:
        print "ERROR:", e
        logger.error("Error delete periodic task after delete scenarios")

def after_delete_periodic_task(mapper, connection, target):
    session = Session()
    print ("after_delete_periodic_task")
    try:
        scenarios = session.query(PeriodicTaskScenarios).filter_by(periodictask_id=target.id).first()
        if scenarios:
            scenarios.periodictask_id = None
            session.add(scenarios)
            session.flush()
    except Exception as e:
        print "ERROR:", e
        logger.error("Error delete periodic task after delete scenarios")

event.listen(PeriodicTask, "after_delete", after_delete_periodic_task)
event.listen(PeriodicTask, "after_insert", after_update)
event.listen(PeriodicTask, "after_update", after_update)
event.listen(PeriodicTask, "before_update", before_update_periodic_task)

event.listen(PeriodicTaskScenarios, "after_delete", after_delete_periodic_task_scenarios)
event.listen(PeriodicTaskScenarios, "after_insert", after_update)
event.listen(PeriodicTaskScenarios, "after_update", after_update)

