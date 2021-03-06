"""
Form Field classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json

from api.base.resources import ValidationError
from sqlalchemy.orm.exc import NoResultFound
from cloudml.utils import isint
from api.amazon_utils import amazon_config


class BaseField(object):
    """
    Base class for all form fields
    """
    def __init__(self, name=None):
        """Build a form field

        Parameters
        ----------
        name : string
            Determines how the field would be named in form's cleaned data.

        """
        self.value = None
        self.name = name

    def clean(self, value):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """
        self.value = value
        return self.value


# TODO: convert to string?
class CharField(BaseField):
    pass


class UniqueNameField(CharField):
    def __init__(self, **kwargs):
        self._model_cls = kwargs.pop('Model')
        self.verbose_name = kwargs.pop('verbose_name', None)
        if self.verbose_name is None:
            from api.base.utils import convert_name
            self.verbose_name = convert_name(
                self._model_cls.__name__, to_text=True)
        super(UniqueNameField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(UniqueNameField, self).clean(value)

        query = self._model_cls.query.filter_by(name=value)
        if self.obj.id:
            query = query.filter(self._model_cls.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError(
                "{0} with name \"{1}\" already exist. "
                "Please choose another one.".format(self.verbose_name, value))
        return value


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
        except (ValueError, TypeError) as e:
            raise ValidationError('should be integer number', e)


class ChoiceField(CharField):
    def __init__(self, **kwargs):
        self._choices = kwargs.pop('choices')
        super(ChoiceField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(ChoiceField, self).clean(value)

        if value and value not in self._choices:
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

        if not isint(value):
            raise ValidationError('Invalid {0} id: {1}'.format(
                self.Model.__name__, value))

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

        values = value.split(',')
        for item in values:
            if not isint(item):
                raise ValidationError('Invalid {0} id: {1}'.format(
                    self.Model.__name__, item))

        self.models = self.Model.query.filter(
            self.Model.id.in_(values)).all()
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
            except ValueError as e:
                raise ValidationError(
                    'JSON file is corrupted. Can not load it: %s' % value, e)


class FeaturesField(BaseField):
    def clean(self, value):
        if value is not None:
            if value:
                from cloudml.trainer.config import FeatureModel, \
                    SchemaException
                try:
                    value = json.loads(value)
                    feature_model = FeatureModel(
                        json.dumps(value), is_file=False)
                except SchemaException, exc:
                    raise ValidationError(
                        'Features JSON file is invalid: %s' % exc, exc)
                except ValueError, e:
                    raise ValidationError(
                        'JSON file is corrupted. Can not load it: %s' % value,
                        e)
            else:
                # features came, but value is empty
                raise ValidationError('Features JSON should not be empty')
        return value


class ImportHandlerFileField(BaseField):
    import_params = None

    def clean(self, value):
        if value is None:
            return

        value = value.encode('utf-8')
        from cloudml.importhandler.importhandler import ExtractionPlan
        from api.amazon_utils import amazon_config
        try:
            plan = ExtractionPlan(value, is_file=False)
            plan.amazon_settings = amazon_config()
            self.import_params = plan.inputs.keys()
            self.import_handler_type = 'xml'
        except Exception as exc:
            raise ValidationError(exc.message, exc)
        return value


class ScriptFileField(BaseField):

    def clean(self, value):
        if value is None:
            return

        value = value.encode('utf-8')
        from cloudml.importhandler.importhandler import ScriptManager
        try:
            s = ScriptManager()
            s.add_python(value)
        except Exception as exc:
            raise ValidationError(exc.message, exc)
        return value


class ScriptUrlField(BaseField):

    def clean(self, value):
        if value is None:
            return

        value = value.encode('utf-8')
        from cloudml.importhandler.importhandler import Script, ScriptManager
        from api.import_handlers.models import XmlScript
        from api.amazon_utils import amazon_config
        try:
            xml_scr = XmlScript(data=value, type=XmlScript.TYPE_PYTHON_FILE)
            s = Script(xml_scr.to_xml())
            s.amazon_settings = amazon_config()
            manager = ScriptManager()
            manager.add_python(s.get_script_str())
        except Exception as exc:
            raise ValidationError(exc.message, exc)
        return value


# TODO: Use ModelField after removing JSON Import handlers
class ImportHandlerField(CharField):  # pragma: no cover
    def clean(self, value):
        if value:
            if 'xml' in value:
                from api.models import XmlImportHandler
                value = XmlImportHandler.query.get(
                    value.replace('xml', ''))
            elif 'json' in value:
                from api.models import ImportHandler
                value = ImportHandler.query.get(value.replace('json', ''))
        return value
