from api.base.forms.base_forms import BaseChooseInstanceAndDataset, \
    CharField, ModelField, ChoiceField
from api.base.resources import ValidationError
from api.models import DataSet, TestResult, Instance, Model


class AddTestForm(BaseChooseInstanceAndDataset):
    HANDLER_TYPE = 'test'

    aws_instance = ModelField(model=Instance, return_model=True)
    dataset = ModelField(model=DataSet, return_model=True)
    parameters = CharField()
    spot_instance_type = ChoiceField(choices=BaseChooseInstanceAndDataset.TYPE_CHOICES)
    format = ChoiceField(choices=DataSet.FORMATS)

    name = CharField()
    model_id = CharField()

    def before_clean(self):
        self.model = Model.query.get(self.model_id)

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

        from tasks import run_test
        from api.import_handlers.tasks import import_data
        instance = self.cleaned_data.get('aws_instance', None)
        spot_instance_type = self.cleaned_data.get('spot_instance_type', None)

        if self.params_filled:
            # load and train
            import_handler = test.model.test_import_handler
            params = self.cleaned_data.get('parameters', None)
            dataset = import_handler.create_dataset(
                params,
                data_format=self.cleaned_data.get(
                    'format', DataSet.FORMAT_JSON)
            )
            import_data.apply_async(kwargs={'dataset_id': dataset.id,
                                            'test_id': test.id},
                                    link=run_test.subtask(args=(test.id, ),
                                    options={'queue': instance.name}))
        else:
            # test using dataset
            dataset = self.cleaned_data.get('dataset', None)
            run_test.apply_async(([dataset.id],
                                  test.id,),
                                  queue=instance.name)

        return test
