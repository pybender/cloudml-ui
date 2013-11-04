from copy import deepcopy
from datetime import datetime
from collections import Iterable

from api.base.fields import BaseField
from api.resources import ValidationError


def get_declared_items(bases, attrs, cls=BaseField):
    """
    Creates a list of Field instances.
    """
    items = []
    for name, obj in attrs.items():
        if not isinstance(obj, cls):
            continue

        if hasattr(obj, "name") and obj.name:
            obj.option = obj.name
        else:
            obj.option = name
        items.append((obj.option, attrs.pop(name)))
       
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

    NO_REQUIRED_FOR_EDIT = False  # don't validate required fields if obj specified
    required_fields = ()  # list of required fields

    # could be used with tabs edit forms, where we can spec. one 
    # group of the fields or another one.
    required_fields_groups = {}
    group_chooser = None

    def __init__(self, data=None, obj=None, Model=None,
                 data_from_request=True, prefix='', no_required=False,
                 model_name=None, **kwargs):
        self.fields = dict(deepcopy(self.base_fields))
        self.forms = dict(deepcopy(self.base_forms))
        self.errors = []
        self.prefix = prefix
        self._cleaned = False
        self.no_required = no_required
        self.filled = False
        self.inner_name = None
        self.obj = None

        if self.required_fields and self.required_fields_groups:
            raise ValueError('Either required fields or groups should be specified')

        if self.required_fields_groups:
            if not self.group_chooser:
                raise ValueError('Specify group_chooser')

        if obj is not None:
            self.obj = obj
            if self.NO_REQUIRED_FOR_EDIT:
                self.no_required = True
        elif Model:
            self.obj = Model()
        elif model_name:
            self.model_name = model_name
        else:
            raise ValueError('Either obj or Model should be specified')

        self.set_data(from_request() if data_from_request else data)

        # Setting extra parameters
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    def append_data(self, key, val):
        self.data = self.data or {}
        self.data[key] = val

    def set_data(self, data):
        self.data = data or {}
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
        if self.inner_name:
            return errors
        return 'Here is some validation errors: %s' % errors

    @property
    def is_edit(self):
        return hasattr(self.obj, "_id") and bool(self.obj._id)

    def is_valid(self):
        if not self._cleaned:
            self.clean()
        return not bool(self.errors)

    def clean(self):
        if self.obj is None and self.model_name:
            from api import app
            callable_model = getattr(app.db, self.model_name)
            self.obj = callable_model()

        def add_error(name, msg):
            if self.inner_name:
                field_name = '%s-%s' % (self.inner_name, name)
            else:
                field_name = name
            self.errors.append({'name': field_name, 'error': msg})

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
                add_error(name, str(exc))

            if value is not None:
                self.cleaned_data[name] = value
                self.filled = True

        try:
            self.validate_data()
        except ValidationError, exc:
            add_error("fields", str(exc))

        if not self.no_required:
            # Check required fields
            for fields in self.required_fields:
                is_valid = check_required(fields, self.cleaned_data)
                if not is_valid:
                    if isinstance(fields, str):
                        field = fields
                        add_error(field, '%s is required' % field)
                    else:
                        add_error("fields", 'either one of fields %s is required' % ', '.join(fields))

        for name, form in self.forms.iteritems():
            try:
                #form.no_required = True
                form.inner_name = name
                # TODO: make possible to choose whether form field is required
                if form.is_valid() and form.filled:
                    self.cleaned_data[name] = form.save(commit=False)
            except ValidationError, exc:
                if form.filled:
                    self.errors.append({'name': '%s' % name, 'error': str(exc)})

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
            self.obj.save(validate=True, check_keys=False)

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


def check_required(obj, cd):
    if isinstance(obj, str):
        val = cd.get(obj)
        if not val:
            return False

    elif isinstance(obj, Iterable):
        # check whether one of specified fields is filled
        is_valid = False
        for item in obj:
            if cd.get(item) is not None:
                is_valid = True
                break

        if not is_valid:
            return False
    else:
        raise ValueError()

    return True
