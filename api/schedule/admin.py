from flask.ext.admin.form import Select2Field
from api import app, celery, admin
from api.base.admin import BaseAdmin
from .models import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule)
from .tasks import *

class PeriodicTaskAdmin(BaseAdmin):
    Model = PeriodicTask
    MIX_METADATA = False

    form_overrides = {
        'task': Select2Field
    }

    tasks = app.scheduletasks.keys()
    names = ["%s (%s)" % (n.split('.')[-1], '.'.join(n.split('.')[0:-1])) for n in tasks]

    form_args = dict(
        task=dict(
            choices = zip(tasks, names)
        )
    )
    def after_model_change(self, form, model, is_created):
        # TODO: nader20141214, we still dont have a way to set the request user
        print ('Save start 01')
        model.save()

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