import json

from api.base.resources import ValidationError
from sqlalchemy.orm.exc import NoResultFound


class BaseField(object):

    def __init__(self, name=None):
        self.value = None
        self.name = name

    def clean(self, value):
        self.value = value
        return self.value


# TODO: convert to string?
class CharField(BaseField):
    pass


class BooleanField(BaseField):
    TRUE_VALUES = ['true', 'True', 1, '1', u'1']

    def clean(self, value):
        value = super(BooleanField, self).clean(value)
        if value is not None:
            return value in self.TRUE_VALUES
        return None


class IntegerField(BaseField):
    def clean(self, value):
        value = super(IntegerField, self).clean(value)
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValidationError('should be integer number')


class ChoiceField(CharField):
    def __init__(self, **kwargs):
        self._choices = kwargs.pop('choices')
        super(ChoiceField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(ChoiceField, self).clean(value)

        if value and not value in self._choices:
            raise ValidationError(
                'Should be one of %s' % ', '.join(self._choices))

        return value


# TODO: could we use ModelField?
class DocumentField(CharField):  # pragma: no cover
    def __init__(self, **kwargs):
        self.Model = kwargs.pop('doc')
        self.by_name = kwargs.pop('by_name', False)
        self.return_doc = kwargs.pop('return_doc', False)
        self.filter_params = kwargs.pop('filter_params', {})
        super(DocumentField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(DocumentField, self).clean(value)

        if value is not None and value != u'undefined':
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
        self.model = None
        self.Model = kwargs.pop('model')
        self.return_model = kwargs.pop('return_model', False)
        super(ModelField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(ModelField, self).clean(value)

        if value is None:
            return None

        self.model = self.Model.query.get(value)
        if self.model is None:
            raise ValidationError(
                '{0} not found'.format(self.Model.__name__))

        return self.model if self.return_model else value


class MultipleModelField(CharField):
    def __init__(self, **kwargs):
        self.models = []
        self.Model = kwargs.pop('model')
        self.return_model = kwargs.pop('return_model', False)
        super(MultipleModelField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(MultipleModelField, self).clean(value)

        if not value:
            return None

        self.models = self.Model.query.filter(
            self.Model.id.in_(value.split(','))).all()
        if not self.models:
            raise ValidationError('{0} not found'.format(
                self.Model.__name__))

        return self.models if self.return_model else value


class JsonField(CharField):
    def clean(self, value):
        value = super(JsonField, self).clean(value)

        if value:
            try:
                return json.loads(value)
            except ValueError:
                raise ValidationError(
                    'JSON file is corrupted. Can not load it: %s' % value)


class ImportHandlerFileField(BaseField):
    def clean(self, value):
        self.import_params = None
        self.import_handler_type = 'json'

        if not value:
            return

        # parsing the json import handler
        json_parsed = False
        try:
            data = json.loads(value)
            json_parsed = True
        except ValueError, exc:
            pass

        if json_parsed:
            try:
                from core.importhandler.importhandler import ExtractionPlan, \
                    ImportHandlerException
                plan = ExtractionPlan(value, is_file=False)
                self.import_params = plan.input_params
                return data
            except (ValueError, ImportHandlerException) as exc:
                raise ValidationError(
                    'Import Handler JSON file is invalid: %s' % exc)
        else:
            value = value.encode('utf-8')
            try:
                from core.xmlimporthandler.importhandler import ExtractionPlan
                plan = ExtractionPlan(value, is_file=False)
                self.import_params = plan.inputs.keys()
                self.import_handler_type = 'xml'
            except Exception as exc:
                raise ValidationError(exc)
        return value


# TODO: Use ModelField after removing JSON Import handlers
class ImportHandlerField(CharField):  # pragma: no cover
    def clean(self, value):
        if value:
            if 'xml' in value:
                from api.models import XmlImportHandler
                value = XmlImportHandler.query.get(
                    value.replace('xml', ''))
            else:
                from api.models import ImportHandler
                value = ImportHandler.query.get(value)
        return value
