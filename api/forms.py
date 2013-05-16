import json
from datetime import datetime

from api.resources import ValidationError


class BaseForm():
    def __init__(self, data, obj=None):
        self.data = data
        self.errors = []
        self.obj = obj
        self._cleaned = False

    @property
    def error_messages(self):
        return ','.join(self.errors)

    def is_valid(self):
        if not self._cleaned:
            self.clean()
        return not bool(self.errors)

    def clean(self):
        self.cleaned_data = {}
        for name in self.fields:
            value = self.data.get(name, None)
            mthd = "clean_%s" % name
            if hasattr(self, mthd):
                value = getattr(self, mthd)(value)
            if value:
                self.cleaned_data[name] = value
        self._cleaned = True
        return self.cleaned_data

    def save(self):
        if not self.obj:
            raise Exception('Spec obj')

        if not self.is_valid():
            raise ValidationError(self.errors)

        for name, val in self.cleaned_data.iteritems():
            setattr(self.obj, name, val)

        self.updated_on = datetime.now()
        self.obj.save(validate=True)

        return self.obj


class ModelEdit(BaseForm):
    fields = ('importhandler', 'train_importhandler',
              'example_id', 'example_label')

    def clean_importhandler(self, value):
        if value and not value == 'undefined':
            return json.loads(value)

    clean_train_importhandler = clean_importhandler
