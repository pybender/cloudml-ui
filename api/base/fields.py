import json

from api.resources import ValidationError
from sqlalchemy.orm.exc import NoResultFound


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
            raise ValidationError('Should be one of %s' % ', '.join(self._choices))

        return value


class DocumentField(CharField):
    def __init__(self, **kwargs):
        self.Model = kwargs.pop('doc')
        self.by_name = kwargs.pop('by_name', False)
        self.return_doc = kwargs.pop('return_doc', False)
        self.filter_params = kwargs.pop('filter_params', {})
        super(DocumentField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(DocumentField, self).clean(value)

        if value is not None:
            params = {'name' if self.by_name else 'id': value}
            params.update(self.filter_params)

            try:
                obj = self.Model.query.filter_by(**params)[0]
            except:
                raise ValidationError('Document not found')

            if self.return_doc:
                return obj
            else:
                self.doc = obj
                return value


class ModelField(CharField):
    def __init__(self, **kwargs):
        self.Model = kwargs.pop('model')
        self.by_name = kwargs.pop('by_name', False)
        self.return_model = kwargs.pop('return_model', False)
        self.filter_params = kwargs.pop('filter_params', {})
        super(ModelField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(ModelField, self).clean(value)

        if value is not None:
            query = self.Model.query

            if self.by_name:
                query = query.filter_by(name=value)
            else:
                query = query.filter_by(id=value)
            try:
                obj = query.one()
            except NoResultFound:
                obj = None
            if obj is None:
                raise ValidationError('{0} not found'.format(
                    self.Model.__name__))

            if self.return_model:
                return obj
            else:
                self.model = obj
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
