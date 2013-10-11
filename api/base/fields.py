import json

from api.resources import ValidationError


class BaseField(object):
    DEFAULT_VALUE = None

    def __init__(self, default=None, name=None):
        self.value = None
        self.name = name
        self._default = default or self.DEFAULT_VALUE

    def clean(self, value):
        self.value = value
        return self.value


class CharField(BaseField):
    pass


class BooleanField(BaseField):
    def clean(self, value):
        value = super(BooleanField, self).clean(value)
        if value is not None:
            return value == 'true' or value == 'True' or value == True
        return None


class ChoiceField(CharField):
    def __init__(self, **kwargs):
        self._choices = kwargs.pop('choices')
        super(ChoiceField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(ChoiceField, self).clean(value)

        if value and not value in self._choices:
            raise ValidationError('should be one of %s' % ', '.join(self._choices))

        return value


class DocumentField(CharField):
    def __init__(self, **kwargs):
        self.document_name = kwargs.pop('doc')
        self.by_name = kwargs.pop('by_name', False)
        self.return_doc = kwargs.pop('return_doc', False)
        self.filter_params = kwargs.pop('filter_params', {})
        super(DocumentField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(DocumentField, self).clean(value)

        if value:
            if self.by_name:
                params = {'name': value}
            else:
                from bson.objectid import ObjectId
                params = {'_id': ObjectId(value)}
            params.update(self.filter_params)

            from api import app
            callable_model = getattr(app.db, self.document_name)
            obj = callable_model.find_one(params)
            if obj is None:
                raise ValidationError('Document not found')

            if self.return_doc:
                return obj
            else:
                self.doc = obj
                return value


class JsonField(CharField):
    def clean(self, value):
        value = super(JsonField, self).clean(value)

        if value:
            try:
                return json.loads(value)
            except ValueError:
                raise ValidationError('invalid json: %s' % value)


class ImportHandlerFileField(BaseField):
    def clean(self, value):
        self.import_params = None
        if not value:
            return

        from core.importhandler.importhandler import ExtractionPlan, \
            ImportHandlerException
        try:
            data = json.loads(value)
        except ValueError, exc:
            raise ValidationError('Invalid data: %s' % exc)

        try:
            plan = ExtractionPlan(value, is_file=False)
            self.import_params = plan.input_params
        except (ValueError, ImportHandlerException) as exc:
            raise ValidationError('Invalid importhandler: %s' % exc)

        return data
