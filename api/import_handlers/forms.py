import json

from api.base.forms import BaseForm
from api.base.fields import CharField, JsonField, ChoiceField
from api.resources import ValidationError
from api.models import DataSet, ImportHandler
from core.importhandler.importhandler import ImportHandlerException,\
    ExtractionPlan


class BaseImportHandlerForm(BaseForm):
    def clean_data(self, value, field):
        if not value:
            return

        try:
            plan = ExtractionPlan(json.dumps(value), is_file=False)
            self.cleaned_data['import_params'] = plan.input_params
        except (ValueError, ImportHandlerException) as exc:
            raise ValidationError('Invalid importhandler: %s' % exc)

        return value


class ImportHandlerEditForm(BaseImportHandlerForm):
    name = CharField()
    data = JsonField()


class ImportHandlerAddForm(BaseImportHandlerForm):
    name = CharField()
    type = ChoiceField(choices=ImportHandler.TYPES)
    data = JsonField()
    import_params = JsonField()


class DataSetAddForm(BaseForm):
    required_fields = ('format', 'import_params')
    format = ChoiceField(choices=DataSet.FORMATS)
    import_params = JsonField()

    def before_clean(self):
        self.importhandler = ImportHandler.query.get(self.import_handler_id)

    def save(self, commit=True):
        from api.tasks import import_data

        dataset = super(DataSetAddForm, self).save(commit=False)

        str_params = "-".join(["%s=%s" % item
                              for item in dataset.import_params.iteritems()])
        dataset.name = "%s: %s" % (self.importhandler.name, str_params)
        dataset.import_handler_id = self.importhandler.id
        dataset.save()
        dataset.set_file_path()
        import_data.delay(str(dataset._id))
        return dataset


class DataSetEditForm(BaseForm):
    name = CharField()
