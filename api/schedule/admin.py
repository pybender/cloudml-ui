from flask_admin.form import Select2Field
from wtforms.fields import TextAreaField
from api import app, admin
from api.base.admin import BaseAdmin
from api.models import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule, PeriodicTaskScenarios)
from .tasks import *
from .fields import SelectScenariosTask, JSONField


class PeriodicTaskScenariosAdmin(BaseAdmin):
    Model = PeriodicTaskScenarios
    create_template = 'admin/schedule/create.html'
    edit_template = 'admin/schedule/edit.html'

    MIX_METADATA = False
    column_list = ['id', 'name', 'enabled', 'status', 'interval', 'crontab', 'created_on', 'updated_on', 'created_by', 'updated_by']
    form_overrides = {
        'descriptions': TextAreaField,
        'scenarios': JSONField,
        'crontab': JSONField,
        'interval': JSONField,
    }

    form_widget_args = {
        'descriptions': {
            'rows': 10,
            'style': 'width: 720px; height: 100px;'
        },
        'scenarios': {
            'rows': 1,
            'style': 'width: 720px; height: 3px;'
        },
        'crontab': {
            'rows': 5,
            'style': 'width: 720px; height: 3px;',
            'data-error': 'Error 1'
        },
        'interval': {
            'rows': 5,
            'style': 'width: 720px; height: 3px;',
            'data-error': 'Error 2'
        },
        'error': {
            'disabled':'disabled',
            'style': 'width: 720px;'
        },
        'status': {
            'disabled':'disabled'
        },
        'periodictask_id': {
            'disabled':'disabled'
        }
    }
    # form_create_rules = [ rules.Field('name'), rules.Field('descriptions'), rules.Field('crontab'), rules.Field('interval') ]
    # form_args = { 'crontab' : { 'validators': [try_crontab_interval] }, 'interval': { 'validators':[try_crontab_interval] } }

    def on_model_change(self, form, model, is_created):
        print ("on_model_change", form, model, is_created)

    def after_model_change(self, form, model, is_created):
        model.status = model.STATUS_NEW
        model.save()

admin.add_view(PeriodicTaskScenariosAdmin(
    name='Scenarios', category='Schedule'))

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
    # TODO Cannot change scenarios schedule task name
    #def on_model_change (self, form, model, is_created): print ("on_model_change", model) try: old_name = get_history(model, 'name')[2][0] new_name = get_history(model, 'name')[0][0] if old_name != new_name: print ("on_model_change", new_name, old_name) except: pass

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