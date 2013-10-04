from copy import deepcopy
from datetime import datetime

from api.base.fields import BaseField
from api.resources import ValidationError



def get_declared_items(bases, attrs, cls=BaseField):
    """
    Creates a list of Field instances.
    """
    items = [(name, attrs.pop(name))
                 for name, obj in attrs.items()
                 if isinstance(obj, cls)]
    for name, item in items:
        item.option = name
    return items


class InternalForm(object):
    pass


class DeclarativeFieldsMetaclass(type):
    """
    Meta class that converts Variable attributes to a dictionary called
    'base_fields' and Schemas to a dictionary called 'base_schemas'.
    """
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = get_declared_items(bases, attrs)
        attrs['base_forms'] = get_declared_items(bases, attrs, cls=InternalForm)
        return super(DeclarativeFieldsMetaclass,
                     cls).__new__(cls, name, bases, attrs)


class BaseForm(InternalForm):
    """
    Base class for any Form.
    """
    __metaclass__ = DeclarativeFieldsMetaclass

    required_fields = ()  # list of required fields

    # could be used with tabs edit forms, where we can spec. one 
    # group of the fields or another one.
    required_fields_groups = {}
    group_chooser = None

    def __init__(self, data=None, obj=None, Model=None,
                 data_from_request=True, prefix='', **kwargs):
        self.fields = dict(deepcopy(self.base_fields))
        self.forms = dict(deepcopy(self.base_forms))
        self.errors = []
        self.prefix = prefix
        self._cleaned = False

        if obj:
            self.obj = obj
        elif Model:
            self.obj = Model()
        else:
            raise ValueError('Either obj or Model should be specified')

        if self.required_fields and self.required_fields_groups:
            raise ValueError('Either required fields or groups should be specified')

        if self.required_fields_groups:
            if not self.group_chooser:
                raise ValueError('Specify group_chooser')

        self.set_data(from_request() if data_from_request else data)

        # Setting extra parameters
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    def set_data(self, data):
        self.data = data
        if data:
            if self.required_fields_groups:
                self.current_group = self.data.get(self.group_chooser)
                self.required_fields = self.required_fields_groups[self.current_group]

            for name, form in self.forms.iteritems():
                form.set_data(data)

    @property
    def error_messages(self):
        errors = ', '.join(["%s%s" % (err['name'] + ': ' if err['name'] else '', err['error'])
                           for err in self.errors])
        return 'Here is some validation errors: %s' % errors

    def is_valid(self):
        if not self._cleaned:
            self.clean()
        return not bool(self.errors)

    def clean(self):
        self.cleaned_data = {}
        self.before_clean()

        for name, field in self.fields.iteritems():
            value = self.data.get(self.prefix + name, None)

            try:
                value = field.clean(value)
                mthd = "clean_%s" % name
                if hasattr(self, mthd):
                    value = getattr(self, mthd)(value, field)
            except ValidationError, exc:
                self.errors.append({'name': name, 'error': str(exc)})

            if value is not None:
                self.cleaned_data[name] = value

            if name in self.required_fields:
                cleaned_value = self.cleaned_data.get(name)
                if not cleaned_value:
                    self.errors.append({'name': name,
                                        'error': '%s is required' % name})

        try:
            self.validate_data()
        except ValidationError, exc:
            self.errors.append({'name': None, 'error': str(exc)})

        for name, form in self.forms.iteritems():
            try:
                form.clean()
                self.cleaned_data[name] = form.save(commit=False)
            except ValueError, exc:
                self.errors.append({'name': 'Form %s' % name, 'errors': str(exc)})

        if self.errors:
            raise ValidationError(self.error_messages, errors=self.errors)

        self._cleaned = True

        self.after_clean()

        return self.cleaned_data

    def save(self, commit=True):
        if not self.is_valid():
            raise ValidationError(self.errors)

        for name, val in self.cleaned_data.iteritems():
            setattr(self.obj, name, val)

        self.obj.updated_on = datetime.now()
        if commit:
            self.obj.save(validate=True)

        return self.obj

    def validate_data(self):
        pass

    def before_clean(self):
        pass

    def after_clean(self):
        pass


def from_request():
    from flask import request
    data = {}
    for k in request.form.keys():
        data[k] = request.form.get(k, None)
    for k in request.files.keys():
        data[k] = request.files.get(k, None)
    return data
