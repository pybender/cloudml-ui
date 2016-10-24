"""
Forms, that used for adding and edditing XML Import handlers.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.base.forms import BaseForm, CharField, BooleanField, JsonField
from api import app
from api.base.resources import ValidationError

db = app.sql_db


class PeriodicTaskScenariosForm(BaseForm):
    required_fields = ('name', 'scenarios', ('interval', 'crontab'))
    NO_REQUIRED_FOR_EDIT = True

    name = CharField()
    descriptions = CharField()
    scenarios = JsonField()
    interval = JsonField()
    crontab = JsonField()
    enabled = BooleanField()

    def clean_interval(self, value, field):
        if value:
            if 'period' not in value:
                raise ValidationError('Interval should have period value')
            if value['period'] not in ['microseconds', 'seconds', 'minutes',
                                       'hours', 'days']:
                raise ValidationError('Invalid period value')
            if 'every' not in value:
                raise ValidationError('Interval should have an "every" value')
            try:
                every = int(value['every'])
            except Exception as exc:
                raise ValidationError(exc.message, exc)
        return value

    def clean_crontab(self, value, field):
        if value:
            if 'minute' not in value or not value['minute']:
                raise ValidationError('Crontab should have minute value')
            if 'hour' not in value or not value['hour']:
                raise ValidationError('Crontab should have hour value')
            if 'day_of_week' not in value or not value['day_of_week']:
                raise ValidationError('Crontab should have day_of_week value')
            if 'day_of_month' not in value or not value['day_of_month']:
                raise ValidationError('Crontab should have day_of_month value')
            if 'month_of_year' not in value or not value['month_of_year']:
                raise ValidationError('Crontab should have month_of_year value')
        return value

    def clean_scenarios(self, v, field):

        def _validate_task(value):
            if 'type' not in value or value['type'] not in ['single', 'chain',
                                                            'chord', 'group']:
                raise ValidationError('Invalid task type value')
            if value['type'] == 'single':
                if 'tasks' not in value or not len(value['tasks']):
                    raise ValidationError('Single task name is missing')
                if 'kwargs' not in value:
                    raise ValidationError('Task kwargs are missing')
            else:
                if value['type'] == 'chord':
                    if 'callback' not in value or not value['callback']:
                        raise ValidationError('Chord callback is missing')
                    if 'callback_kwargs' not in value:
                        raise ValidationError('Callback kwargs are missing')
                if 'tasks' not in value or not len(value['tasks']):
                    raise ValidationError('%s should contain at least 1 task'
                                          % value['type'])
                    for task in value['tasks']:
                        _validate_task(task)
        if v:
            _validate_task(v)
        return v

    def validate_data(self):
        schedule_type = self.cleaned_data.get('type', None)
        if schedule_type == 'interval':
            self.cleaned_data['crontab'] = {}
        elif schedule_type == 'crontab':
            self.cleaned_data['interval'] = {}
