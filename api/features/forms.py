import json

from api.base.forms import BaseForm, CharField, ChoiceField, BooleanField, \
    JsonField, DocumentField
from api.base.resources import ValidationError
from models import NamedFeatureType, PredefinedClassifier, PredefinedScaler, \
    PredefinedTransformer, FeatureSet, Feature
from api.ml_models.models import Model
from api.base.forms.base_forms import BasePredefinedForm
from api.features.models import CLASSIFIERS


class FeatureParamsMixin(object):
    """
    Mixin for feature params validation depended on feature type
    """
    def _validate_param(self, data, name):
        from core.trainer.feature_types import FEATURE_PARAMS_TYPES

        if not name in data:
            raise ValidationError('Parameter {} is required'.format(name))
        value = data[name]
        param_type = FEATURE_PARAMS_TYPES[name]['type']

        if not value:
            raise ValidationError('Parameter {} is required'.format(name))

        if param_type == 'str':
            pass  # do nothing

        elif param_type == 'text':
            try:
                json.loads(value)
            except ValueError:
                raise ValidationError('invalid json: {}'.format(value))

        elif param_type == 'dict':
            if not isinstance(value, dict):
                raise ValidationError(
                    '{} should be a dictionary'.format(name))
            if not value.keys():
                raise ValidationError(
                    'Map {} should contain at least one value'.format(name))
            for key, val in value.items():
                if not val:
                    raise ValidationError(
                        'Value {0} in {1} can\'t be empty'.format(key, name))

    def clean_params(self, value, field):
        from core.trainer.feature_types import FEATURE_TYPE_FACTORIES

        value_type = self.data.get('type')
        if not type:
            raise ValidationError('invalid type')
        if not value_type in FEATURE_TYPE_FACTORIES:
            return
        required_params = FEATURE_TYPE_FACTORIES[value_type].required_params
        for name in required_params:
            self._validate_param(value, name)
        return value


class NamedFeatureTypeAddForm(BaseForm, FeatureParamsMixin):
    required_fields = ('name', 'type')

    name = CharField()
    type_field = ChoiceField(choices=NamedFeatureType.TYPES_LIST, name='type')
    input_format = CharField()
    params = JsonField()

    def clean_name(self, value, field):
        if not value:
            raise ValidationError('name is required field')

        query = NamedFeatureType.query.filter_by(name=value)
        if self.obj.id:
            query = query.filter(NamedFeatureType.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError(
                'Named feature type with name "%s" already exist. Please choose another one.' % value)
        return value


class FeatureSetForm(BaseForm):
    schema_name = CharField()


class FeatureSetAddForm(BaseForm):
    fields = ('name', 'schema_name', 'classifier', )

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

    def clean_classifier(self, value):
        if not value:
            raise ValidationError('classifier is required')

        classifier = PredefinedClassifier.query.get(value)
        if not classifier:
            raise ValidationError('classifier not found')

        return classifier



class ScalerForm(BasePredefinedForm):
    OBJECT_NAME = 'scaler'
    DOC = PredefinedScaler

    group_chooser = 'predefined_selected'
    required_fields_groups = {'true': ('scaler', ),
                              'false': ('type', ),
                              None: ('type', )}

    name = CharField()
    type_field = ChoiceField(choices=PredefinedScaler.TYPES_LIST, name='type')
    params = JsonField()
    # whether need to copy feature scaler fields from predefined one
    predefined_selected = BooleanField()
    # whether we need to create predefined item (not feature related)
    scaler = DocumentField(doc=PredefinedScaler, by_name=True, return_doc=True)
    feature_id = DocumentField(doc=Feature, by_name=False,
                               return_doc=False)


class ClassifierForm(BasePredefinedForm):
    """
    Form with predefined item selection for model instead of feature
    """
    OBJECT_NAME = 'classifier'
    DOC = PredefinedClassifier

    group_chooser = 'predefined_selected'
    required_fields_groups = {'true': ('classifier', ),
                              'false': ('type', ),
                              None: ('type', )}

    name = CharField()
    type_field = ChoiceField(
        choices=PredefinedClassifier.TYPES_LIST, name='type')
    params = JsonField()
    # whether need to copy model classifier fields from predefined one
    predefined_selected = BooleanField()
    # whether we need to create predefined item (not model-related)
    classifier = DocumentField(
        doc=PredefinedClassifier, by_name=False, return_doc=True)
    model_id = DocumentField(doc=Model, by_name=False, return_doc=False)

    def validate_data(self):
        from config import CLASSIFIERS
        super(ClassifierForm, self).validate_data()

        # TODO: move from here
        def convert_auto_dict(val):
            import ast
            #if val != 'auto':  
            return val

        def convert(val, val_type):
            TYPE_CONVERTORS = {
                'string': lambda a: a,
                'boolean': lambda a: a in ('True', 1, True),
                'float': lambda a: float(a),
                'integer': lambda a: int(a),
                'auto_dict': convert_auto_dict
            }
            return TYPE_CONVERTORS[val_type](val)

        params = self.cleaned_data.get('params')
        if params:
            type_ = self.cleaned_data['type']
            config = CLASSIFIERS[type_]['parameters']
            for param_config in config:
                name = param_config.get('name')
                if name in params:
                    try:
                        params[name] = convert(
                            params[name], param_config.get('type'))
                    except ValueError, exc:
                        raise ValidationError(
                            'Invalid parameter %s value: %s' % (name, exc))


class TransformerForm(BasePredefinedForm):
    OBJECT_NAME = 'transformer'
    DOC = PredefinedTransformer

    group_chooser = 'predefined_selected'
    required_fields_groups = {
        'true': ('transformer', ),
        'false': ('type', ),
        None: ('type', )}

    name = CharField()
    type_field = ChoiceField(
        choices=PredefinedTransformer.TYPES_LIST, name='type')
    params = JsonField()
    predefined_selected = BooleanField()
    transformer = DocumentField(
        doc=PredefinedTransformer, by_name=True, return_doc=True)
    feature_id = DocumentField(doc=Feature, by_name=False,
                               return_doc=False)


class FeatureForm(BaseForm, FeatureParamsMixin):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'type', 'feature_set_id')

    name = CharField()
    type_field = CharField(name='type')
    input_format = CharField()
    params = JsonField()
    required = BooleanField()
    default = CharField()
    is_target_variable = BooleanField()
    feature_set_id = DocumentField(doc=FeatureSet, by_name=False,
                                   return_doc=False)

    transformer = TransformerForm(
        Model=PredefinedTransformer,
        prefix='transformer-', data_from_request=False)
    remove_transformer = BooleanField()
    scaler = ScalerForm(Model=PredefinedScaler, prefix='scaler-',
                        data_from_request=False)
    remove_scaler = BooleanField()

    def clean_type(self, value, field):
        if value and not value in NamedFeatureType.TYPES_LIST:
            # Try to find type in named types
            found = NamedFeatureType.query.filter_by(name=value).count()
            if not found:
                raise ValidationError('invalid type')
        return value

    def clean_remove_scaler(self, value, field):
        return value and self.is_edit

    def clean_remove_transformer(self, value, field):
        return value and self.is_edit

    def save(self, *args, **kwargs):
        remove_transformer = self.cleaned_data.get('remove_transformer', False)
        if remove_transformer and self.obj.transformer:
            self.obj.transformer = None

        remove_scaler = self.cleaned_data.get('remove_scaler', False)
        if remove_scaler and self.obj.scaler:
            self.obj.scaler = None

        return super(FeatureForm, self).save(*args, **kwargs)
