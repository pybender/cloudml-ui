from api import app
from api.base.models import db
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import Base
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

engine = create_engine(app.config['ENGINE_URL'], pool_size=20, pool_recycle=3600)
Session = sessionmaker(bind=engine, autocommit=True)

class ConstraintError(Exception):
    pass

def after_update(mapper, connection, target):
    session = Session()
    if not target.interval and not target.crontab:
        raise ConstraintError('One of interval or crontab must be set.')
    if target.interval and target.crontab:
        raise ConstraintError('Only one of interval or crontab must be set')
    PeriodicTasks.changed(session, target)

#event.listen(PeriodicTask, "before_delete", after_update)
#event.listen(PeriodicTask, "before_insert", after_update)
#event.listen(PeriodicTask, "before_update", after_update)

event.listen(PeriodicTask, "after_delete", after_update)
event.listen(PeriodicTask, "after_insert", after_update)
event.listen(PeriodicTask, "after_update", after_update)