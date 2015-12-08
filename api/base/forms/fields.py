"""
Form Field classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json

from api.base.resources import ValidationError
from sqlalchemy.orm.exc import NoResultFound
from cloudml.utils import isint


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
        except (ValueError, TypeError):
            raise ValidationError('should be integer number')


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
            except ValueError:
                raise ValidationError(
                    'JSON file is corrupted. Can not load it: %s' % value)


class FeaturesField(JsonField):
    def clean(self, value):
        value = super(FeaturesField, self).clean(value)
        if value:
            from cloudml.trainer.config import FeatureModel, SchemaException
            from collections import OrderedDict

            class SimplifiedFeatureModel(FeatureModel):
                def __init__(self, config, is_file=False):
                    try:
                        if is_file:
                            with open(config, 'r') as fp:
                                data = json.load(fp)
                        else:
                            data = json.loads(config)
                    except ValueError as e:
                        raise SchemaException(message='%s %s ' % (config, e))

                    if 'schema-name' not in data:
                        raise SchemaException(message="schema-name is missing")

                    self.schema_name = data['schema-name']
                    self.classifier = {}
                    self.target_variable = None
                    self._named_feature_types = {}
                    self.features = OrderedDict()
                    self.required_feature_names = []
                    self.group_by = []

                    # simplification: classifier should present in config, but
                    # can be empty
                    if 'classifier' not in data:
                        raise SchemaException('Classifier is missing')
                    if data['classifier']:
                        self._process_classifier(data)

                    # Add feature types defined in 'feature-types section
                    if 'feature-types' in data:
                        for feature_type in data['feature-types']:
                            self._process_named_feature_type(feature_type)

                    self.feature_names = []
                    # features should present in config
                    if 'features' not in data:
                        raise SchemaException('Features list is missing')

                    for feature in data['features']:
                        self._process_feature(feature)

                    # simplification: features list can be empty,
                    # so target variable may not set
                    if len(self.feature_names) and self.target_variable is None:
                        raise SchemaException('No target variable defined')

                    group_by = data.get('group-by', None)
                    if group_by:
                        self._process_group_by(group_by)

            try:
                feature_model = SimplifiedFeatureModel(json.dumps(value),
                                                       is_file=False)
            except SchemaException, exc:
                raise ValidationError(
                    'Features JSON file is invalid: %s' % exc)
        return value


class ImportHandlerFileField(BaseField):
    import_params = None

    def clean(self, value):
        if value is None:
            return

        value = value.encode('utf-8')
        from cloudml.importhandler.importhandler import ExtractionPlan
        try:
            plan = ExtractionPlan(value, is_file=False)
            self.import_params = plan.inputs.keys()
            self.import_handler_type = 'xml'
        except Exception as exc:
            raise ValidationError(exc)
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
            elif 'json' in value:
                from api.models import ImportHandler
                value = ImportHandler.query.get(value.replace('json', ''))
        return value
