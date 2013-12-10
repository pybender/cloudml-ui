from api.base.resources import ValidationError
from api.base.forms import BaseForm, ModelField, ChoiceField, \
    CharField, MultipleModelField
from api.base.forms.forms import populate_parser, only_one_required
from api.import_handlers.models import DataSet
from api.instances.models import Instance


class BaseChooseInstanceAndDataset(BaseForm):
    HANDLER_TYPE = 'train'
    TYPE_CHOICES = ('m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge',
                    'hi1.4xlarge', 'hs1.8xlarge')

    aws_instance = ModelField(model=Instance, return_model=True)
    dataset = ModelField(model=DataSet, return_model=True)
    parameters = CharField()
    spot_instance_type = ChoiceField(choices=TYPE_CHOICES)
    format = ChoiceField(choices=DataSet.FORMATS)

    params_filled = False

    def clean_parameters(self, value, field):
        self.params_filled = False
        if self.model is None:
            return

        handler = getattr(self.model, '%s_import_handler' % self.HANDLER_TYPE)
        self.parameter_names = handler.import_params
        parser = populate_parser(self.parameter_names)
        params = parser.parse_args()

        parameters = {}
        missed_params = []
        for name, val in params.iteritems():
            if not val:
                missed_params.append(name)
            else:
                parameters[name] = val
                self.params_filled = True

        if self.params_filled and missed_params:
            raise ValidationError('Parameters %s are required' % ', '.join(missed_params))

        return parameters

    def validate_data(self):
        inst_err = only_one_required(
            self.cleaned_data,
            ('spot_instance_type', 'aws_instance'), raise_exc=False)
        ds_err = only_one_required(
            self.cleaned_data,
            ('parameters', 'dataset'), raise_exc=False)
        fmt_err = only_one_required(
            self.cleaned_data,
            ('format', 'dataset'), raise_exc=False)
        if inst_err or ds_err or fmt_err:
            raise ValidationError('%s%s%s.' %
                (inst_err, '. ' if inst_err else '', ds_err))


class BaseChooseInstanceAndDatasetMultiple(BaseChooseInstanceAndDataset):
    dataset = MultipleModelField(model=DataSet, return_model=True)
