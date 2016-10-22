from .base import Base

import json
import datetime
import logging
from functools import partial

from sqlalchemy.orm import relationship, deferred, backref, foreign, remote
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from sqlalchemy import Index, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import event, and_
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ColumnClause

from celery import schedules
from celery.canvas import signature, chain, group, chord
from celery.utils.log import get_logger
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy_utils.types.choice import ChoiceType

from api.base.models import db, BaseModel, BaseMixin, JSONType, S3File
from api.base.models.models import BaseDeployedEntity
from api.logs.models import LogMessage
from api.amazon_utils import AmazonS3Helper
from api.import_handlers.models import ImportHandlerMixin
from cloudml.trainer.classifier_settings import TYPE_CLASSIFICATION
from api import app, celery
from . import Session

logger = get_logger(__name__)
LOGER_INFO = "%r : %r"

def gettext(message):
    return message
_ = gettext

class ValidationError(Exception):
    pass

class IntervalSchedule(Base):
    __tablename__ = "interval_schedule"
    PERIOD_CHOICES = (('days', 'Days'),
                      ('hours', 'Hours'),
                      ('minutes', 'Minutes'),
                      ('seconds', 'Seconds'),
                      ('microseconds', 'Microseconds'))

    every = Column(Integer, nullable=False)
    period = Column(ChoiceType(PERIOD_CHOICES))
    periodic_tasks = relationship('PeriodicTask')

    @property
    def schedule(self):
        return schedules.schedule(datetime.timedelta(**{self.period.code: self.every}))

    @classmethod
    def from_interval(cls, session, every, period):
        print ("from_interval 00:", every, period)
        obj = cls.filter_by(session, every=every, period=period).first()
        if obj is None:
            obj = cls(every=every, period=period)
            session.add(obj)
        print ("from_interval 01", obj)
        return obj

    @classmethod
    def from_schedule(cls, session, schedule, period='seconds'):
        #TODO not correct period send
        print ("INTERVAL:", schedule, period)
        every = max(schedule.run_every.total_seconds(), 0)
        print ("INTERVAL every:", schedule.run_every, schedule.run_every.total_seconds(), every)
        obj = cls.filter_by(session, every=every, period=period).first()
        if obj is None:
            return cls(every=every, period=period)
        else:
            return obj

    def __str__(self):
        if self.every == 1:
            return _('every {0.period_singular}').format(self)
        return _('every {0.every} {0.period.value}').format(self)

    @property
    def period_singular(self):
        return self.period.value[:-1]
        # return self.period[:-1] - Old give error 'Choice' object has no attribute '__getitem__'

    def save(self):
        pass

class CrontabSchedule(Base):
    """
    Task result/status.
    """
    __tablename__ = "crontab_schedule"
    minute = Column(String(length=120), default="*")
    hour = Column(String(length=120), default="*")
    day_of_week = Column(String(length=120), default="*")
    day_of_month = Column(String(length=120), default="*")
    month_of_year = Column(String(length=120), default="*")
    periodic_tasks = relationship('PeriodicTask')

    def __str__(self):
        rfield = lambda f: f and str(f).replace(' ', '') or '*'
        return '{0} {1} {2} {3} {4} (m/h/d/dM/MY)'.format(
            rfield(self.minute), rfield(self.hour), rfield(self.day_of_week),
            rfield(self.day_of_month), rfield(self.month_of_year),
        )

    @property
    def schedule(self):
        return schedules.crontab(minute=self.minute,
                                 hour=self.hour,
                                 day_of_week=self.day_of_week,
                                 day_of_month=self.day_of_month,
                                 month_of_year=self.month_of_year)

    @classmethod
    def from_schedule(cls, session, schedule):
        spec = {'minute': schedule._orig_minute,
                'hour': schedule._orig_hour,
                'day_of_week': schedule._orig_day_of_week,
                'day_of_month': schedule._orig_day_of_month,
                'month_of_year': schedule._orig_month_of_year}
        obj = cls.filter_by(session, **spec).first()
        if obj is None:
            obj = cls(**spec)
            session.add(obj)

        return obj

    def save(self):
        pass

class PeriodicTasks(Base):
    __tablename__ = "periodic_tasks"

    ident = Column(Integer, default=1, autoincrement=True)
    last_update = Column(DateTime, default=datetime.datetime.utcnow())

    @classmethod
    def changed(cls, session, instance):
        if not instance.no_changes:
            obj, created = cls.update_or_create(session, defaults={'last_update': datetime.datetime.utcnow()}, ident=1)
            session.add(obj)
            session.flush()

    @classmethod
    def last_change(cls, session):
        obj = cls.filter_by(session, ident=1).first()
        return obj.last_update if obj else None

    def save(self):
        pass

class PeriodicTask(Base):
    __tablename__ = "periodic_task"

    name = Column(String(length=120), unique=True)
    task = Column(String(length=254))
    crontab_id = Column(Integer, ForeignKey('crontab_schedule.id'))
    crontab = relationship("CrontabSchedule", back_populates="periodic_tasks")
    interval_id = Column(Integer, ForeignKey('interval_schedule.id'))
    interval = relationship("IntervalSchedule", back_populates="periodic_tasks")
    args = Column(String(length=254))
    kwargs = Column(String(length=254))
    last_run_at = Column(DateTime, default=datetime.datetime.utcnow)
    total_run_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    no_changes = False

    def __str__(self):
        fmt = '{0.name}: {0.crontab}'
        return fmt.format(self)

    @property
    def schedule(self):
        if self.crontab:
            return self.crontab.schedule
        if self.interval:
            return self.interval.schedule

    @property
    def tasks_scenarios(self):
        choices = []
        for task in PeriodicTaskScenarios.query.filter_by(enabled=True).all():
            choices.append((task.id, task.name))
        return choices

    def save(self):
        print ("PeriodicTask save")
        pass

class PeriodicTaskScenarios(BaseModel, db.Model):
    STATUS_NEW = 'New'
    STATUS_QUEUED = 'Queued'
    STATUS_IMPORTED = 'Imported'
    STATUS_CANCELED = 'Canceled'
    STATUS_ERROR = 'Error'
    STATUS_ERROR_PARSER = 'Parser error'
    ScenariosPlayer = 'api.schedule.tasks.scenarios_schedule_task'


    name = db.Column(db.String(100))
    descriptions = db.Column(db.String(254))
    enabled = db.Column(Boolean, default=True)
    no_changes = db.Column(Boolean, default=False)
    error = db.Column(db.String(254), default='')
    status = db.Column(db.String(100), default=STATUS_NEW)
    scenarios = db.Column(JSONType)
    interval = db.Column(JSONType)
    crontab = db.Column(JSONType)

    chorduse = False
    sctasks = None
    celeryregistertask = celery.tasks.keys()
    # celeryregistertask = app.scheduletasks.keys()
    session = None
    # TODO for dev only  start

    def __init__(self, session=None):
        self.session = session or Session()

    @property
    def args(self):
        #try:  args = self.scenarios['args'] except: args = []
        args = []
        return json.dumps(args)

    @property
    def kargs(self):
        kargs = dict(scenario_task_id = self.id)
        #try: if type(self.scenarios['kargs']) is dict: kargs.update(self.scenarios['kargs']) except: pass
        return json.dumps(kargs)

    def schedule_crontab(self, session):
        if self.crontab:
            class scenariosScheduleCr():
                def __init__(self, **kwargs):
                    self._orig_minute = kwargs['orig_minute']
                    self._orig_hour = kwargs['orig_hour']
                    self._orig_day_of_week =  kwargs['orig_day_of_week']
                    self._orig_day_of_month = kwargs['orig_day_of_month']
                    self._orig_month_of_year =  kwargs['orig_month_of_year']
            scschedule = scenariosScheduleCr(
                orig_minute = self.crontab['minute'],
                orig_hour = self.crontab['hour'],
                orig_day_of_week = self.crontab['day_of_week'],
                orig_day_of_month = self.crontab['day_of_month'],
                orig_month_of_year = self.crontab['month_of_year']

            )
            cs = CrontabSchedule.from_schedule(session, scschedule)
        else:
            cs = None
        return cs

    def schedule_interval(self, session):
        if self.interval:
            cs = IntervalSchedule.from_interval(session, self.interval['every'], self.interval['period'])
        else:
            cs = None

        return cs

    def _enable(self):
        self.no_changes = False
        self.enabled = True
        self.save()

    def _disable(self):
        self.no_changes = True
        self.enabled = False
        self.save()
#       self.session.add(model)

#    @staticmethod def save_model(session, obj): session.add(obj)
#    def save(self): super(PeriodicTaskScenarios, self).save()

    def set_status(self, status, commit=True):
        self.status = status
        if status != self.STATUS_ERROR_PARSER:
            self.error = ''
        if commit:
            self.save()

    def set_error(self, error, status,  commit=True):
        self.error = str(error)[:253]
        self.status = status
        if commit:
            self.save()

    def task_parser(self):
        try:
            logger.debug("start task_parser")
            self.sctasks = self._load_tree(self.scenarios)
            self.set_status(self.STATUS_IMPORTED)
            return True
        except Exception as e:
            self.set_error(e, self.STATUS_ERROR_PARSER)
            return False

    def _load_tree(self, tree=None):
        group_tasks = []
        self.celeryregistertask = celery.tasks.keys()
        def get_correct_scenarios_tree(t):
            try:
                tchainname = t.get('chainname', None)
                tname = t.get('name', None)
                ttype = t.get('type', None)
                ttasks = t.get('tasks', None)
                return tchainname, tname, ttype, ttasks
            except:
                raise ValueError('Error validate 02. Invalid input format\
                                  for scenarios.')

        chainname, name, type, tasks = get_correct_scenarios_tree(tree)
        if chainname:
            if not type or not tasks:
                raise ValueError('Error validate 01. Invalid input format \
                                  for scenarios.')
            if len(tasks) == 1:
                group_tasks = self._load_tree(tree=tasks[0])
                if group_tasks.task not in self.celeryregistertask:
                    raise ValueError('Error validate 03. Task name: {0!r} \
                                      not register in Celery'.format(group_tasks))
            else:
                for elm in tasks:
                    task = self._load_tree(tree=elm)
                    if task:
                        if task.task not in self.celeryregistertask:
                            raise ValueError('Error validate 04. Task name: {0!r}\
                                              not register in Celery'.format(group_tasks))
                        group_tasks.append(task)
        if name:
            type = 'single'
            args = tree.get('args', [])
            kwargs = tree.get('kwargs', {})
            group_tasks = signature(name, args=args, kwargs=kwargs)
            if group_tasks.task not in self.celeryregistertask:
                raise ValueError('Error validate 05. Task name: {0!r}\
                                  not register in Celery'.format(group_tasks))

        if type == 'chain':
            return chain(group_tasks)
        elif type == 'group':
            return group(group_tasks)
        elif type == 'chord':
            if self.chorduse:
                raise ValueError('Error validate 08. "Chord" type can\
                                  used once in scenarios: {0!r}.'.format(chainname))
            self.chorduse = True
            callback = tree.get('callback', None)
            if not callback:
                raise ValueError('Error validate 06. Not callback\
                                  function for chord group: {0!r}.'.format(chainname))
            name = callback.get('name', [])
            args = callback.get('args', [])
            kwargs = callback.get('kwargs', {})
            return group(group_tasks) | signature(name, args=args, kwargs=kwargs)
        elif type == 'single':
            return group_tasks
        else:
            raise ValueError('Error validate 07. Not correct\
                              group type for tasks: {0!r}.'.format(chainname))

    def __str__(self):
        return self.name