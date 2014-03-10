"""# DataSet forms"""
from api.import_handlers.models import DataSet, ImportHandler
from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField, \
    DocumentField


class DataSetAddForm(BaseForm):
    required_fields = ('format', )
    format = ChoiceField(choices=DataSet.FORMATS)
    import_params = JsonField()
    handler_type = ChoiceField(choices=('XML', 'Simple'))

    @property
    def is_xml(self):
        return self.data.get('handler_type') == 'XML'

    def before_clean(self):
        if self.is_xml:
            self.importhandler = XmlImportHandler.query.get(self.import_handler_id)
        else:
            self.importhandler = ImportHandler.query.get(self.import_handler_id)

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

        dataset = super(DataSetAddForm, self).save(commit=False)

        str_params = "-".join(["%s=%s" % item
                              for item in dataset.import_params.iteritems()])
        dataset.name = "%s: %s" % (self.importhandler.name, str_params)
        if self.is_xml:
            dataset.xml_import_handler_id = self.importhandler.id
        else:
            dataset.import_handler_id = self.importhandler.id
        dataset.compress = True
        dataset.save()
        dataset.set_file_path()
        import_data.delay(str(dataset.id))
        return dataset


class DataSetEditForm(BaseForm):
    name = CharField()
