import json
import logging
from multiprocessing.util import Finalize

from api import app, celery
from api.base.models import db

from celery import schedules
from celery.beat import ScheduleEntry, Scheduler
from celery.utils.log import get_logger
from celery.utils.encoding import safe_str
from celery.utils.timeutils import is_naive

from models import (PeriodicTaskScenarios, PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule, Session)
#Session = db.session

DEFAULT_MAX_INTERVAL = 5
logger = get_logger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
ADD_ENTRY_ERROR = """\
Couldn't add entry %r to database schedule: %r. Contents: %r
"""
LOGER_INFO = """\
%r : %r
"""

class ModelEntry(ScheduleEntry):
    model_schedules = ((schedules.crontab, CrontabSchedule, 'crontab'),
                       (schedules.schedule, IntervalSchedule, 'interval'))
    save_fields = ['last_run_at', 'total_run_count', 'no_changes']

    def __init__(self, model, session=None):
        self.app = celery
        self.session = session or Session()
        self.name = model.name
        self.task = model.task
        self.schedule = model.schedule
        self.args = json.loads(model.args or '[]')
        self.kwargs = json.loads(model.kwargs or '{}')
        self.total_run_count = model.total_run_count
        self.model = model
        self.options = {}  # need reconstruction
        if not model.last_run_at:
            model.last_run_at = self._default_now()
        orig = self.last_run_at = model.last_run_at
        if not is_naive(self.last_run_at):
            self.last_run_at = self.last_run_at.replace(tzinfo=None)
        assert orig.hour == self.last_run_at.hour  # timezone sanity

    def _disable(self, model):
        model.no_changes = True
        model.enabled = False
        self.session.add(model)

    def is_due(self):
        if not self.model.enabled:
            return False, 5.0   # 5 second delay for re-enable.
        return self.schedule.is_due(self.last_run_at)

    def _default_now(self):
        return self.app.now()

    def __next__(self):
        self.model.last_run_at = self.app.now()
        self.model.total_run_count += 1
        self.model.no_changes = True
        return self.__class__(self.model)

    next = __next__  # for 2to3

    def save(self):
        obj = PeriodicTask.filter_by(self.session, id=self.model.id).first()
        for field in self.save_fields:
            setattr(obj, field, getattr(self.model, field))
        self.save_model(self.session, obj)

    @staticmethod
    def save_model(session, obj):
        session.add(obj)

    @classmethod
    def to_model_schedule(cls, schedule, session):
        for schedule_type, model_type, model_field in cls.model_schedules:
            schedule = schedules.maybe_schedule(schedule)
            if isinstance(schedule, schedule_type):
                model_schedule = model_type.from_schedule(session, schedule)
                cls.save_model(session, model_schedule)
                return model_schedule, model_field
        raise ValueError('Cannot convert schedule type {0!r} to model'.format(schedule))

    @classmethod
    def from_entry(cls, name, session, skip_fields=('relative', 'options'), **entry):
        fields = dict(entry)
        for skip_field in skip_fields:
            fields.pop(skip_field, None)
        schedule = fields.pop('schedule')
        model_schedule, model_field = cls.to_model_schedule(schedule, session)
        fields[model_field] = model_schedule
        fields['args'] = json.dumps(fields.get('args') or [])
        fields['kwargs'] = json.dumps(fields.get('kwargs') or {})
        model, _ = PeriodicTask.update_or_create(session, name=name, defaults=fields)
        cls.save_model(session, model)
        return cls(model)

    def __repr__(self):
        return '<ModelEntry: {0} {1}(*{2}, **{3}) {{4}}>'.format(
            safe_str(self.name), self.task, self.args, self.kwargs, self.schedule,
        )

class CloudmluiDatabaseScheduler(Scheduler):
    sync_every = 5

    Entry = ModelEntry
    Model = PeriodicTask
    Changes = PeriodicTasks
    Scenarios = PeriodicTaskScenarios

    _schedule = None
    _last_timestamp = None
    _initial_read = False

    def __init__(self, initcelery = 'INIT', session=None, *args, **kwargs):
        logger.info("Start Cloudmlui celery beat database scheduler...")
        self.session = session or Session()
        self._cureenttasks = {}
        self._dirty = set()
        self._finalize = Finalize(self, self.sync, exitpriority=5)
        logger.debug(LOGER_INFO, 'args', args)
        logger.debug(LOGER_INFO, 'kwargs', kwargs)
        super(CloudmluiDatabaseScheduler, self).__init__(*args, **kwargs)
        self.max_interval = (kwargs.get('max_interval') or
                             self.app.conf.CELERYBEAT_MAX_LOOP_INTERVAL or
                             DEFAULT_MAX_INTERVAL)

        celery.databasescheduler = self
        #print ("celery.tasks", celery.tasks)
    #TODO 1.0 Make correct delete celery beat task.

    def setup_schedule(self):
        logger.debug('CloudmluiDatabaseScheduler setup_schedule...')
        self.install_default_entries({})
        self.update_from_dict(self.app.conf.CELERYBEAT_SCHEDULE)
        self.update_from_db(self.schedule)

    def install_default_entries(self, data):
        logger.debug('CloudmluiDatabaseScheduler install_default_entries...')
        entries = {}
        if self.app.conf.CELERY_TASK_RESULT_EXPIRES:
            entries.setdefault(
                'celery.backend_cleanup', {
                    'task': 'celery.backend_cleanup',
                    'schedule': schedules.crontab('*/5', '*', '*'),
                    'options': {'expires': 12 * 3600},
                },
            )
        self.update_from_dict(entries)

    def update_from_db(self, data):
        logger.debug('CloudmluiDatabaseScheduler update_from_db...')
        entries = {}
        self.update_from_dict(entries)

    def update_from_dict(self, dict_):
        logger.debug('CloudmluiDatabaseScheduler update_from_dict...')
        s = {}
        for name, entry in dict_.items():
            try:
                self._cureenttasks[name] = 1

            except Exception as exc:
                logger.error(ADD_ENTRY_ERROR, name, exc, entry)
        self.schedule.update(s)

    def all_as_schedule(self):
        logger.debug('CloudmluiDatabaseScheduler: all_as_schedule')
        s = {}
        for model in self.Model.filter_by(self.session, enabled=True).all():
            try:
                s[model.name] = self.Entry(model)
            except Exception as e:
                logger.error(e)
        for scenarios in self.session.query(self.Scenarios).filter_by(enabled=True).all():
            try:
                model = self.session.query(self.Model).filter_by(name=scenarios.name).first()
                if not model:
                    model = self.Model()
                    model.name = scenarios.name
                    model.task = scenarios.ScenariosPlayer

                model.args = scenarios.args
                model.kwargs = scenarios.kargs

                if scenarios.crontab:
                    cs = scenarios.schedule_crontab(self.session)
                    if cs:
                        model.crontab_id = cs.id
                        model.crontab = cs
                    else:
                        raise ValueError('Cannot get crontab for scenarios {0!r} to model'.format(scenarios.name))
                elif scenarios.interval:
                    cs = scenarios.schedule_interval(self.session)
                    if cs:
                        model.interval_id = cs.id
                        model.interval = cs
                    else:
                        raise ValueError('Cannot get interval for scenarios {0!r} to model'.format(scenarios.name))
                else:
                    raise ValueError('Cannot get interval or crontab for scenarios {0!r} to model'.format(scenarios.name))
                self.session.add(model)
                self.session.flush()
                scenarios.periodictask_id = model.id
                self.session.add(scenarios)
                self.session.flush()
                s[model.name] = self.Entry(model)
            except Exception as e:
                import sys
                import traceback
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                logger.error(e)
        return s

    def schedule_changed(self):
        logger.debug('CloudmluiDatabaseScheduler schedule_changed...')
        last, ts = self._last_timestamp, self.Changes.last_change(self.session)
        try:
            if ts and ts > (last if last else ts):
                return True
        finally:
            self._last_timestamp = ts
        return False

    def reserve(self, entry):
        logger.debug('CloudmluiDatabaseScheduler reserve...')
        new_entry = Scheduler.reserve(self, entry)
        self._dirty.add(new_entry.name)
        return new_entry

    def sync(self):
        logger.debug('CloudmluiDatabaseScheduler - sync...')
        _tried = set()
        while self._dirty:
            try:
                name = self._dirty.pop()
                _tried.add(name)
                self.schedule[name].save()
            except KeyError:
                logger.error("sync key error ")

    def update_from_dict(self, dict_):
        logger.debug('CloudmluiDatabaseScheduler update_from_dict...')
        s = {}
        for name, entry in dict_.items():
            try:
                s[name] = self.Entry.from_entry(name, self.session, **entry)
            except Exception as exc:
                logger.error(ADD_ENTRY_ERROR, name, exc, entry)
        self.schedule.update(s)

    @property
    def schedule(self):
        update = False
        if not self._initial_read:
            logger.debug('CloudmluiDatabaseScheduler schedule (property): intial read')
            update = True
            self._initial_read = True
        elif self.schedule_changed():
            logger.debug('CloudmluiDatabaseScheduler schedule (property): schedule_changed True.')
            update = True

        if update:
            logger.debug('CloudmluiDatabaseScheduler schedule (property): UPDATE all_as_schedule.')
            self.sync()
            self._schedule = self.all_as_schedule()
            logger.debug('Current schedule:\n%s', '\n'.join(repr(entry) for entry in self._schedule.itervalues()))
        return self._schedule
