import sqlalchemy

from api.base.resources import ValidationError
from api.base.forms import BaseForm, ModelField, ChoiceField, \
    CharField, MultipleModelField, BooleanField, JsonField
from api.base.forms.forms import populate_parser, only_one_required
from api.import_handlers.models import DataSet
from api.instances.models import Instance


class BaseChooseInstanceAndDataset(BaseForm):
    HANDLER_TYPE = 'train'
    TYPE_CHOICES = ('m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge',
                    'hi1.4xlarge', 'hs1.8xlarge')

    new_dataset_selected = BooleanField()
    existing_instance_selected = BooleanField()
    aws_instance = ModelField(model=Instance, return_model=True)
    dataset = ModelField(model=DataSet, return_model=True)
    parameters = JsonField()
    spot_instance_type = ChoiceField(choices=TYPE_CHOICES)
    format = ChoiceField(choices=DataSet.FORMATS)

    def clean_parameters(self, params, field):
        params = params or {}
        if self.model is None:
            return params

        if not isinstance(params, dict):
            raise ValidationError('Invalid parameters format')
        return params

    def validate_data(self):
        # DataSet tab
        new_dataset_selected = self.cleaned_data.get('new_dataset_selected')
        if new_dataset_selected:
            if not self.cleaned_data.get('format'):
                self.add_error("format", "Please select format of the Data Set")

            handler = getattr(self.model, '%s_import_handler' % self.HANDLER_TYPE)
            parameter_names = handler.import_params
            if parameter_names and len(parameter_names) > 0:  # No params for this import handler
                parameters = self.cleaned_data.get('parameters')
                missed_params = set(parameter_names) - set(parameters.keys())
                if missed_params:
                    self.add_error(
                        "parameters",
                        "Some parameters are missing: %s" % ', '.join(missed_params))
        else:
            if not self.cleaned_data.get('dataset'):
                self.add_error("dataset", "Please select Data Set")
            
        # Instance tab
        existing_instance_selected = self.cleaned_data.get('existing_instance_selected')
        if existing_instance_selected:
            if not self.cleaned_data.get('aws_instance'):
                self.add_error("aws_instance", "Please select instance with a worker")
        else:
            if not self.cleaned_data.get('spot_instance_type'):
                self.add_error("spot_instance_type", "Please select Spot instance type")


class BaseChooseInstanceAndDatasetMultiple(BaseChooseInstanceAndDataset):
    dataset = MultipleModelField(model=DataSet, return_model=True)


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
        predefined_selected = self.cleaned_data.get(
            'predefined_selected', False)
        feature_id = self.cleaned_data.get('feature_id', False)
        model_id = self.cleaned_data.get('model_id', False)

        # It would be predefined obj, when model, feature not specified
        # and this form will not used as inner form of another one
        self.cleaned_data['is_predefined'] = is_predefined = \
            not (feature_id or model_id or self.inner_name)

        if predefined_selected and is_predefined:
            raise ValidationError(
                'item could be predefined or copied from predefined')

        if is_predefined:
            name = self.cleaned_data.get('name', None)
            if not name:
                raise ValidationError('name is required for predefined item')

            items = self.DOC.query.filter_by(name=name)
            if self.obj.id:
                items = items.filter(
                    sqlalchemy.not_(self.DOC.id == self.obj.id))
            count = items.count()

            if count:
                self.add_error('name', 'Predefined %s with same name already exist. Please choose another one.' % self.OBJECT_NAME)

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

    def save_inner(self):
        obj = self.save()
        return obj.to_dict()

    def save(self):
        commit = self.cleaned_data['is_predefined']
        obj = super(BasePredefinedForm, self).save(commit, commit)
        feature = self.cleaned_data.get('feature', None)
        if feature:
            setattr(feature, self.OBJECT_NAME, obj.to_dict())
            feature.save()

        model = self.cleaned_data.get('model', None)
        if model:
            setattr(model, self.OBJECT_NAME, obj.to_dict())
            model.save()

        return obj
