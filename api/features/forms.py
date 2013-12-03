import json
import sqlalchemy

from api.base.forms import BaseForm
from api.base.fields import CharField, ChoiceField, BooleanField, JsonField, DocumentField
from api.resources import ValidationError
from models import NamedFeatureType, PredefinedClassifier, PredefinedScaler, \
    PredefinedTransformer, FeatureSet, Feature
from api.ml_models.models import *


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


class BasePredefinedForm(BaseForm):
    """
    Base form for creating/edditing features specific items, which could be:
        * predefined item - that could be used when creating/edditing
            feature item to copy fields from them
        * feature item like feature transformer, scaler, etc
            when item fields are specified
        * feature item copied from predefined item.
    """
    # name of the feature field of this item or POST/PUT parameter of the
    # predefined item to copy fields from, when `predefined_selected`.
    OBJECT_NAME = None
    DOC = None

    def clean_feature_id(self, value, field):
        if value:
            self.cleaned_data['feature'] = field.doc
        return value

    def clean_model_id(self, value, field):
        if value:
            self.cleaned_data['model'] = field.doc
        return value

    def validate_data(self):
        predefined_selected = self.cleaned_data.get('predefined_selected', False)
        feature_id = self.cleaned_data.get('feature_id', False)
        model_id = self.cleaned_data.get('model_id', False)

        # It would be predefined obj, when model, feature not specified
        # and this form will not used as inner form of another one
        self.cleaned_data['is_predefined'] = is_predefined = \
                not (feature_id or model_id or self.inner_name)

        if predefined_selected and is_predefined:
            raise ValidationError('item could be predefined or copied from predefined')

        if is_predefined:
            name = self.cleaned_data.get('name', None)
            if not name:
                raise ValidationError('name is required for predefined item')

            items = self.DOC.query.filter_by(name=name)
            if self.obj.id:
                items = items.filter(
                    sqlalchemy.not_(PredefinedTransformer.id == self.obj.id))
            count = items.count()

            if count:
                raise ValidationError('name of predefined item should be unique')

        if predefined_selected:
            obj = self.cleaned_data.get(self.OBJECT_NAME, None)
            if obj:
               self._fill_predefined_values(obj)

    def _fill_predefined_values(self, obj):
        """
        Fills fields from predefined obj
        """
        self.cleaned_data['name'] = obj.name
        self.cleaned_data['type'] = obj.type
        self.cleaned_data['params'] = obj.params

    def save(self, commit=True):
        commit = self.cleaned_data['is_predefined']
        obj = super(BasePredefinedForm, self).save(commit)
        feature = self.cleaned_data.get('feature', None)
        if feature:
            setattr(feature, self.OBJECT_NAME, obj)
            feature.save()

        model = self.cleaned_data.get('model', None)
        if model:
            setattr(model, self.OBJECT_NAME, obj)
            model.save()

        return obj


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
    type_field = ChoiceField(choices=PredefinedClassifier.TYPES_LIST, name='type')
    params = JsonField()
    # whether need to copy model classifier fields from predefined one
    predefined_selected = BooleanField()
    # whether we need to create predefined item (not model-related)
    classifier = DocumentField(doc=PredefinedClassifier, by_name=False, return_doc=True)
    model_id = DocumentField(doc=Model, by_name=False, return_doc=False)


class TransformerForm(BasePredefinedForm):
    OBJECT_NAME = 'transformer'
    DOC = PredefinedTransformer

    group_chooser = 'predefined_selected'
    required_fields_groups = {
        'true': ('transformer', ),
        'false': ('type', ),
        None: ('type', )}

    name = CharField()
    type_field = ChoiceField(choices=PredefinedTransformer.TYPES_LIST, name='type')
    params = JsonField()
    predefined_selected = BooleanField()
    transformer = DocumentField(doc=PredefinedTransformer, by_name=True, return_doc=True)
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

    transformer = TransformerForm(Model=PredefinedTransformer,
                                  prefix='transformer-', data_from_request=False)
    remove_transformer = BooleanField()
    scaler = ScalerForm(Model=PredefinedScaler, prefix='scaler-',
                        data_from_request=False)
    remove_scaler = BooleanField()

    def clean_transformer(self, value, form):
        return value.to_dict()

    def clean_scaler(self, value, form):
        return value.to_dict()

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
