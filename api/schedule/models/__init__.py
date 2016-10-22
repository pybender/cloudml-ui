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
def before_delete_periodic_task_scenarios(mapper, connection, target):
    session = Session()
    try:
        print ("before_delete_periodic_task_scenarios:", target)
        task = PeriodicTask.filter_by(session, name=target.name).first()
        print ("task 01:", task, task.name)
        print ("task 02:", app)
        from celery.events.state import State
        tasks = State().tasks_by_time()
        #from celery import current_app         all_task_names = current_app.tasks.keys()         all_tasks = current_app.tasks.values()         all_task_classes = [type(task) for task in current_app.tasks.itervalues()]

        from celery.task.control import inspect
        i = inspect()
        active = i.active()
        reserved = i.reserved()
        registered = i.registered()
        #state = State().tasks_by_type(task.name)
        print (active, reserved, registered)
        if active:
            for task in active:
                print ("task active", task)
        if reserved:
            for task in reserved:
                print ("task reserved", task)
        if registered:
            for task in registered:
                print ("task registered", task)

        raise ConstraintError('STOP before_delete_periodic_task_scenarios')
    except Exception as e:
        print ("ERROR:", e)
        logger.error("Error delete periodic task from celery")
        raise ConstraintError('STOP before_delete_periodic_task_scenarios')

# celery.events.state.State().tasks_by_type(task.name)]
def after_delete_periodic_task_scenarios(mapper, connection, target):
    session = Session()
    try:
        task = session.query(PeriodicTask).filter_by(name=target.name)
        print ("task 00:", task, task.name)

        #task_id
        #revoke(task_id, terminate=True, signal="KILL")
        if task:
            task.delete()
            # revoke(task_id, terminate=True, signal="KILL")
    except Exception as e:
        logger.error("Error delete periodic task after delete scenarios")


event.listen(PeriodicTask, "after_delete", after_update)
event.listen(PeriodicTask, "after_insert", after_update)
event.listen(PeriodicTask, "after_update", after_update)
event.listen(PeriodicTask, "before_update", before_update_periodic_task)

event.listen(PeriodicTaskScenarios, "after_delete", after_delete_periodic_task_scenarios)
event.listen(PeriodicTaskScenarios, "after_insert", after_update)
event.listen(PeriodicTaskScenarios, "after_update", after_update)
event.listen(PeriodicTaskScenarios, "before_delete", before_delete_periodic_task_scenarios)
