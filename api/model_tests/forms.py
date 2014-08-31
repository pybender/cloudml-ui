from api.base.forms.base_forms import BaseChooseInstanceAndDataset, \
    CharField, ModelField, ChoiceField
from api.base.resources import ValidationError
from api.models import DataSet, TestResult, Instance, Model
from api.base.forms import BaseForm, JsonField

class AddTestForm(BaseChooseInstanceAndDataset):
    HANDLER_TYPE = 'test'

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
        new_dataset_selected = self.cleaned_data.get('new_dataset_selected')
        instance = self.cleaned_data.get('aws_instance', None)
        if new_dataset_selected:  # load and test
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
        else:  # run test with existing dataset
            dataset = self.cleaned_data.get('dataset')
            run_test.apply_async(([dataset.id],
                                  test.id,),
                                  queue=instance.name)
        return test

class SelectFieldsForCSVForm(BaseForm):
    """
    Form containing one json entry called fields which is an array of fields to
    use for generating test examples csv in _put_csv_task_action
    """
    required_fields = ('fields',)
    fields = JsonField()