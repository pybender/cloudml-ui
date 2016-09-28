"""
Features related forms
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json

from api.base.forms import BaseForm, CharField, ChoiceField, BooleanField, \
    JsonField, DocumentField, UniqueNameField
from api.base.forms.base_forms import ParametersConvertorMixin
from api.base.resources import ValidationError
from models import NamedFeatureType, PredefinedClassifier, PredefinedScaler, \
    FeatureSet, Feature
from api.ml_models.models import Model, Transformer
from api.ml_models.forms import FeatureTransformerForm
from api.base.forms.base_forms import BasePredefinedForm
from api.features.models import CLASSIFIERS
from cloudml.trainer.feature_types import FEATURE_TYPE_FACTORIES, \
    InvalidFeatureTypeException, FEATURE_PARAMS_TYPES
from cloudml.utils import isfloat, isint


class FeatureParamsMixin(object):
    """
    Mixin for feature params validation depended on feature type
    """
    def _validate_param(self, data, name):
        value = data.get(name, None)
        if value is None:
            raise ValidationError('Parameter {} is required'.format(name))

        param_type = FEATURE_PARAMS_TYPES[name]['type']
        if param_type == 'int':
            if not isint(value):
                raise ValidationError('{} - int is required'.format(value))

        elif param_type == 'str':
            pass  # do nothing

        elif param_type == 'text':
            if isinstance(value, basestring):
                try:
                    data[name] = json.loads(value)
                except ValueError as e:
                    raise ValidationError('invalid json: {}'.format(value), e)

        elif param_type == 'dict':
            if not isinstance(value, dict):
                raise ValidationError(
                    '{} should be a dictionary'.format(name))
            if not value.keys():
                raise ValidationError(
                    'Map {} should contain at least one value'.format(name))
            for key, val in value.items():
                if not len(str(val)):
                    raise ValidationError(
                        'Value {0} in {1} can\'t be empty'.format(key, name))
        elif param_type == 'list':
            if not isinstance(value, basestring):
                raise ValidationError(
                    '{} should be a list'.format(name))

    def _clean_param(self, data, name):
        param_type = FEATURE_PARAMS_TYPES[name]['type']
        value = data.get(name, None)
        if param_type == 'dict':
            new_dict = {}
            for key, val in value.iteritems():
                if isint(val):
                    new_dict[key] = int(val)
                elif isfloat(val):
                    new_dict[key] = float(val)
                else:
                    new_dict[key] = val
            return new_dict
        elif param_type == 'int':
            return int(value)
        elif param_type == 'boolean':
            return bool(value)
        elif param_type == 'list':
            return list(json.loads(value))
        else:
            return value

    def clean_params(self, value, field):
        value_type = self.data.get('type')
        if value_type is None and not self.NO_REQUIRED_FOR_EDIT:
            raise ValidationError('invalid type')
        if value_type not in FEATURE_TYPE_FACTORIES:
            return
        required_params = FEATURE_TYPE_FACTORIES[value_type].required_params
        optional_params = FEATURE_TYPE_FACTORIES[value_type].optional_params
        if required_params and value is None:
            raise ValidationError('Parameters are required for type {0}, '
                                  'but was not specified'.format(value_type))
        data = {}
        for name in required_params:
            self._validate_param(value, name)
            data[name] = self._clean_param(value, name)
        for name in optional_params:
            v = value.get(name, None)
            if v not in ['', None]:
                self._validate_param(value, name)
                data[name] = self._clean_param(value, name)
        return data


class NamedFeatureTypeForm(BaseForm, FeatureParamsMixin):
    required_fields = ('name', 'type')

    name = UniqueNameField(Model=NamedFeatureType)
    type_field = ChoiceField(choices=NamedFeatureType.TYPES_LIST, name='type')
    input_format = CharField()
    params = JsonField()

    def validate_data(self):
        if self.errors:
            return

        # Trying to make instance of the type
        type_ = self.cleaned_data.get('type')
        type_factory = FEATURE_TYPE_FACTORIES.get(type_)
        try:
            params = self.cleaned_data.get('params') or {}
            input_format = self.cleaned_data.get('params') or 'plain'
            type_factory.get_instance(params, input_format)
        except InvalidFeatureTypeException, exc:
            self.add_error("type", 'Cannot create instance of '
                           'feature type: {0}'.format(exc), exc)


class FeatureSetForm(BaseForm):
    schema_name = CharField()
    group_by = JsonField()
    target_variable = CharField()

    target_feature = None

    def clean_group_by(self, value, field):
        if value is not None:
            ids = [feature['id'] for feature in value]
            return Feature.query.filter(Feature.id.in_(ids)).all()

    def clean_target_variable(self, value, field):
        if value:
            self.target_feature = Feature.query.filter_by(
                name=value,
                feature_set_id=self.id).one()
            if self.target_feature is None:
                raise ValidationError('Feature not found')
        return value

    def save(self):
        self.cleaned_data['modified'] = True
        if self.target_feature:
            self.target_feature.is_target_variable = True
            self.target_feature.required = True
            self.target_feature.save(commit=False)
        return super(FeatureSetForm, self).save()


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


class ClassifierForm(BasePredefinedForm, ParametersConvertorMixin):
    """
    Form for one of this cases (dependly of parameters):
        1. adding/edditing predifined classifier
        2. edditing specific model classifier
        3. copying classifier config from predefined one
           to the model's classifier.
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
        super(ClassifierForm, self).validate_data()

        params = self.cleaned_data.get('params')
        if params:
            from config import CLASSIFIERS
            self.convert_params(self.cleaned_data['type'],
                                params,
                                configuration=CLASSIFIERS)


class FeatureForm(BaseForm, FeatureParamsMixin):
    """
    Feature add/edit form.
    """
    # we could edit only one feature field.
    # no need to fill all of them for edit
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
    disabled = BooleanField()

    transformer = FeatureTransformerForm(
        Model=Transformer,
        prefix='transformer-', data_from_request=False)
    remove_transformer = BooleanField()
    scaler = ScalerForm(Model=PredefinedScaler, prefix='scaler-',
                        data_from_request=False)
    remove_scaler = BooleanField()

    def validate_data(self):
        from numpy import nan
        feature_set_id = self.cleaned_data.get('feature_set_id')
        name = self.cleaned_data.get('name')
        query = Feature.query.filter_by(
            name=name,
            feature_set_id=feature_set_id)
        if self.obj.id:
            query = query.filter(Feature.id != self.obj.id)
        count = query.count()
        if count:
            self.add_error('name', 'Feature with name "%s" already \
exist. Please choose another one.' % name)
            return

        # Validating feature type and parameters
        def get_field_value(name):
            value = self.cleaned_data.get(name)
            if value is None and self.is_edit:
                return getattr(self.obj, name)
            return value

        feature_type = get_field_value('type')
        type_factory = FEATURE_TYPE_FACTORIES.get(feature_type)
        if type_factory:  # inline type
            try:
                params = get_field_value('params')
                input_format = get_field_value('input_format') or 'plain'
                type_ = type_factory.get_instance(params, input_format)
                default = self.cleaned_data.get('default', None)
                if default:
                    self.cleaned_data['default'] = type_.transform(default)
                    if self.cleaned_data['default'] is nan:
                        self.add_error(
                            "default",
                            "Incorrect default value {0} for type {1}. "
                            .format(default, feature_type))
            except InvalidFeatureTypeException, exc:
                self.add_error("type", 'Cannot create instance of '
                               'feature type: {0}'.format(exc), exc)
        else:
            # look into named feature types
            named_type = NamedFeatureType.query.filter_by(
                name=feature_type).first()
            if named_type is None:
                self.add_error('type', 'type is required')

    def clean_type(self, value, field):
        if value and value not in NamedFeatureType.TYPES_LIST:
            # Try to find type in named types
            found = NamedFeatureType.query.filter_by(name=value).count()
            if not found:
                raise ValidationError('invalid type')
        return value

    def clean_remove_scaler(self, value, field):
        return value and self.is_edit

    def clean_remove_transformer(self, value, field):
        return value and self.is_edit

    def clean_required(self, value, field):
        target_variable = self.cleaned_data.get('is_target_variable', None)
        if target_variable or \
                (self.obj.is_target_variable and target_variable is None):
            return True
        return value

    def clean_disabled(self, value, field):
        target_variable = self.cleaned_data.get('is_target_variable', None)
        if target_variable or \
                (self.obj.is_target_variable and target_variable is None):
            return False
        return value

    def clean_is_target_variable(self, value, field):
        if self.obj.is_target_variable and not value:
            feature_set_id = self.cleaned_data.get('feature_set_id')
            query = Feature.query.filter_by(
                feature_set_id=feature_set_id)
            if self.obj.id:
                query = query.filter(Feature.id != self.obj.id)
            features = query.all()
            t_variable = None
            for feature in features:
                if feature.is_target_variable:
                    t_variable = feature.name
            if not t_variable:
                raise ValidationError('Target variable is not set for model '
                                      'feature set. Edit another feature in '
                                      'order to change target variable')
        return value

    def save(self, *args, **kwargs):
        remove_transformer = self.cleaned_data.get('remove_transformer', False)
        if remove_transformer and self.obj.transformer:
            self.obj.transformer = None

        remove_scaler = self.cleaned_data.get('remove_scaler', False)
        if remove_scaler and self.obj.scaler:
            self.obj.scaler = None

        return super(FeatureForm, self).save(*args, **kwargs)
