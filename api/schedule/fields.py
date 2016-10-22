import json
from flask_admin.form import Select2Field, Select2TagsField, rules
from flask_admin.form.widgets import Select2Widget
from flask_admin._compat import text_type, as_unicode
from wtforms import widgets
from wtforms.compat import text_type
from wtforms.widgets.core import HTMLString, html_params
from wtforms.fields import TextAreaField

from api.models import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule, PeriodicTaskScenarios)

class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()

class JSONField(TextAreaField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data:
            # prevent utf8 characters from being converted to ascii
            return as_unicode(json.dumps(self.data, ensure_ascii=False))
        else:
            return ''
    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0]
            # allow saving blank field as None
            if not value:
                self.data = None
                return
            try:
                self.data = json.loads(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext('Invalid JSON'))

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
