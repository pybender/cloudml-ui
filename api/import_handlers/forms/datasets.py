""" DataSet forms"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.import_handlers.models import DataSet, \
    XmlImportHandler as ImportHandler
from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField


class DataSetAddForm(BaseForm):
    required_fields = ('format', )
    format = ChoiceField(choices=DataSet.FORMATS)
    import_params = JsonField()

    def before_clean(self):
        self.importhandler = ImportHandler.query.get(
            self.import_handler_id)

    def clean_import_params(self, value, field):
        if not isinstance(value, dict):
            raise ValidationError('Should be a dictionary')

        for param in self.importhandler.import_params:
            if param not in value:
                raise ValidationError(
                    '{0!s} parameter is required'.format(param))

        return value

    def save(self, commit=True):
        from api.import_handlers.tasks import import_data
        dataset = self.importhandler.create_dataset(
            params=self.cleaned_data['import_params'],
            data_format=self.cleaned_data['format'],
            compress=True)
        dataset.save()
        import_data.delay(dataset.id)
        return dataset


class DataSetEditForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', )
    name = CharField()
