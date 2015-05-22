""" DataSet forms"""
from api.import_handlers.models import DataSet, ImportHandler, XmlImportHandler
from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField, \
    DocumentField


class DataSetAddForm(BaseForm):
    required_fields = ('format', )
    format = ChoiceField(choices=DataSet.FORMATS)
    import_params = JsonField()
    handler_type = ChoiceField(choices=('XML', 'JSON'))

    @property
    def import_handler_cls(self):
        if self.data.get('handler_type') == 'XML':
            return XmlImportHandler
        else:
            return ImportHandler

    def before_clean(self):
        self.importhandler = self.import_handler_cls.query.get(
            self.import_handler_id)

    def clean_import_params(self, value, field):
        if not isinstance(value, dict):
            raise ValidationError('Should be a dict')

        for param in self.importhandler.import_params:
            if param not in value:
                raise ValidationError(
                    '{0!s} not found in import_params'.format(param))

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
    name = CharField()
