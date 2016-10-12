from flask_admin.form import Select2Field, Select2TagsField
from flask_admin.form.widgets import Select2Widget
from sqlalchemy.orm import scoped_session, sessionmaker, sessionmaker
from cgi import escape
from wtforms.compat import text_type
from wtforms.widgets.core import HTMLString, html_params

from api import app, admin
from api.base.admin import BaseAdmin
from api.base.models import db
from api.models import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule, PeriodicTaskScenarios)
from .tasks import *

class PeriodicTaskScenariosAdmin(BaseAdmin):
    Model = PeriodicTaskScenarios
    MIX_METADATA = False

    def after_model_change(self, form, model, is_created):
        #model.scenarios = {'name':model.name, 'chains':[{'chainname':'chain_1', ''}]}
        model.scenarios = {'mainname':model.name,
                           'type':'chain',
                           'tasks':[
                                    {'chainname':'Start upload header',
                                     'type':'chain',
                                     'tasks':[
                                                { 'chainname':'Read header',
                                                  'type':'chain',
                                                  'tasks':[
                                                             { 'chainname':'Get name header',
                                                               'type':'chord',
                                                               'tasks':[{'chainname': 'task.0.1', 'type':'single', 'tasks':['api.schedule.tasks.test_chord_01']},
                                                                        {'chainname': 'task.0.2', 'type':'single', 'tasks':['api.schedule.tasks.test_chord_02']}],
                                                               'callback': 'api.schedule.tasks.test_chord_03'
                                                               },
                                                             { 'chainname':'Upload header',
                                                               'type':'chain',
                                                               'tasks':[{'chainname': 'task.1.1', 'type':'single', 'tasks':['api.schedule.tasks.test_chain_01']},
                                                                        {'chainname': 'task.1.2', 'type':'single', 'tasks':['api.schedule.tasks.test_chain_02']},
                                                                        {'chainname': 'task.1.3', 'type':'single', 'tasks':['api.schedule.tasks.test_chain_01']},
                                                                        {'chainname': 'task.1.4', 'type':'single', 'tasks':['api.schedule.tasks.test_chain_02']}
                                                                        ]
                                                               },
                                                             { 'chainname': 'Finish upload',
                                                               'type':'single',
                                                               'tasks':['api.schedule.tasks.test_chain_01']
                                                               }
                                                  ]
                                                }
                                             ]
                                     },
                                    {'chainname':'Train model',
                                     'type':'single',
                                     'tasks':['api.schedule.tasks.test_single_01']
                                     }
                                  ]
                           }
        model.save()

admin.add_view(PeriodicTaskScenariosAdmin(
    name='Scenarios', category='Schedule'))

class Select2ScenariosWidget(Select2Widget):
    def __call__(self, field, **kwargs):
        allow_blank = getattr(field, 'allow_blank', False)

        kwargs['data-role'] = u'select2'

        if allow_blank and not self.multiple:
            kwargs['data-allow-blank'] = u'1'
        print ("Select2ScenariosWidget")
        return super(Select2ScenariosWidget, self).__call__(field, **kwargs)

class SelectScenariosTask(Select2Field):
    def __init__(self, label='Scenarios', validators=None, coerce=text_type,
                 choices=None, allow_blank=True, blank_text=None, **kwargs):
        self.allow_blank = allow_blank
        self.blank_text = ''

        super(Select2Field, self).__init__(
            label, validators, coerce, choices, **kwargs
        )

    def process_data(self, value):
        self.choices = PeriodicTask().tasks_scenarios
        self.data = None

    def iter_choices(self):
        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is None)
        for value, label in self.choices:
            yield (value, label, self.coerce(value) == self.data)

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] == '__None':
                self.data = None
            else:
                try:
                    self.data = int(valuelist[0])
                except ValueError:
                    raise ValueError(self.gettext(u'Invalid Choice: could not Scenarios Task'))
        else:
            self.data = None

    def pre_validate(self, form):
        if self.data is None:
            return
        super(Select2Field, self).pre_validate(form)

    def populate_obj(self, obj, name):
        if self.data:
            kwargs = '{"task":"%s"}' % self.data
            setattr(obj, 'kwargs', kwargs)

class PeriodicTaskAdmin(BaseAdmin):
    Model = PeriodicTask
    MIX_METADATA = False

    form_overrides = {
        'task': Select2Field
    }

    form_extra_fields = {
        'tasks_scenarios': SelectScenariosTask()
    }

    tasks = app.scheduletasks.keys()
    names = ["%s (%s)" % (n.split('.')[-1], '.'.join(n.split('.')[0:-1])) for n in tasks]

    form_args = dict(
        task=dict(
            choices = zip(tasks, names)
        )
    )

    def after_model_change(self, form, model, is_created):
        model.save()

    def on_model_delete(self, model):
        pass

admin.add_view(PeriodicTaskAdmin(
    name='Periodic Task', category='Schedule'))

class CrontabScheduleAdmin(BaseAdmin):
    Model = CrontabSchedule
    MIX_METADATA = False

admin.add_view(CrontabScheduleAdmin(
    name='Crontab Schedule', category='Schedule'))

class PeriodicTasksAdmin(BaseAdmin):
    Model = PeriodicTasks
    MIX_METADATA = False

admin.add_view(PeriodicTasksAdmin(
    name='Periodic Tasks', category='Schedule'))

class IntervalScheduleAdmin(BaseAdmin):
    Model = IntervalSchedule
    MIX_METADATA = False

    form_overrides = {
        'period': Select2Field
    }

    form_args = dict(
        period=dict(
            choices = IntervalSchedule.PERIOD_CHOICES
        )
    )

admin.add_view(IntervalScheduleAdmin(
    name='Interval Schedule', category='Schedule'))

#PeriodicTask

"""
class ConstraintError(Exception):
    pass
@event.listens_for(Session, "before_flush")
def before_flush_listens_for(session, flush_context, instances):
    print("__________________________________________________________________________")
    print("before_flush")
    for obj in session.new | session.dirty:
        if isinstance(obj, PeriodicTask):
            print ('before_flush PeriodicTask', obj)
            if not obj.interval and not obj.crontab:
                raise ConstraintError('One of interval or crontab must be set.')
            if obj.interval and obj.crontab:
                raise ConstraintError('Only one of interval or crontab must be set')
            PeriodicTasks.changed(session, obj)
"""