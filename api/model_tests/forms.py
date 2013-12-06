from bson import ObjectId

from api import app
from api.base.forms import BaseForm
from api.base.fields import CharField, DocumentField, ModelField, ChoiceField
from api.resources import ValidationError
from api.models import DataSet, TestResult, Instance
from api.forms import populate_parser, only_one_required


# TODO: move to the 'base'
class BaseChooseInstanceAndDataset(BaseForm):
    HANDLER_TYPE = 'train'
    TYPE_CHOICES = ('m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge',
                    'hi1.4xlarge', 'hs1.8xlarge')

    aws_instance = ModelField(model=Instance, return_model=True)
    dataset = DocumentField(doc='DataSet', return_doc=True)
    parameters = CharField()
    spot_instance_type = ChoiceField(choices=TYPE_CHOICES)
    format = ChoiceField(choices=DataSet.FORMATS)

    params_filled = False

    def clean_parameters(self, value, field):
        self.params_filled = False
        if self.model is None:
            return

        handler = getattr(self.model, '%s_import_handler' % self.HANDLER_TYPE)
        self.parameter_names = handler['import_params']
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

    def validate_obj(self):
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


class AddTestForm(BaseChooseInstanceAndDataset):
    HANDLER_TYPE = 'test'

    aws_instance = ModelField(model=Instance, return_model=True)
    dataset = DocumentField(doc='DataSet', return_doc=True)
    parameters = CharField()
    spot_instance_type = ChoiceField(choices=BaseChooseInstanceAndDataset.TYPE_CHOICES)
    format = ChoiceField(choices=DataSet.FORMATS)

    name = CharField()
    model_id = CharField()

    def before_clean(self):
        self.model = app.db.Model.find_one({'_id': ObjectId(self.model_id)})

    def clean_name(self, value, field):
        total = TestResult.query.filter_by(model_id=self.model_id).count()
        return "Test%s" % (total + 1)

    def clean_model_id(self, value, field):
        if self.model is None:
            raise ValidationError('Model not found')

        if not self.model.example_id:
            raise ValidationError('Please fill in "Examples id field name"')

        self.cleaned_data['model_name'] = self.model.name
        self.cleaned_data['model_id'] = self.model_id
        return None

    def save(self, *args, **kwargs):
        test = super(AddTestForm, self).save(commit=False)
        test.status = test.STATUS_QUEUED
        test.examples_fields = \
                self.model.test_import_handler.get_fields()
        test.save()

        from api.tasks import run_test, import_data
        instance = self.cleaned_data.get('aws_instance', None)
        spot_instance_type = self.cleaned_data.get('spot_instance_type', None)

        if self.params_filled:
            # load and train
            from api.models import ImportHandler
            import_handler = ImportHandler(test.model.test_import_handler)
            params = self.cleaned_data.get('parameters', None)
            dataset = import_handler.create_dataset(
                params,
                data_format=self.cleaned_data.get(
                    'format', DataSet.FORMAT_JSON)
            )
            import_data.apply_async(kwargs={'dataset_id': str(dataset._id),
                                            'test_id': str(test.id)},
                                    link=run_test.subtask(args=(str(test.id), ),
                                    options={'queue': instance.name}))
        else:
            # test using dataset
            dataset = self.cleaned_data.get('dataset', None)
            run_test.apply_async(([str(dataset._id),],
                                  str(test.id),),
                                  queue=instance.name)

        return test
