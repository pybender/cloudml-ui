import json

from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField, \
    DocumentField
from models import DataSet, ImportHandler, PredefinedDataSource
from core.importhandler.importhandler import ImportHandlerException,\
    ExtractionPlan


# DataSource forms

class PredefinedDataSourceForm(BaseForm):
    name = CharField()
    type_field = ChoiceField(
        choices=PredefinedDataSource.TYPES_LIST, name='type')
    db = JsonField()

    def clean_name(self, value, field):
        query = PredefinedDataSource.query.filter_by(name=value)
        if self.obj.id:
            query = query.filter(PredefinedDataSource.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError(
                'Data Source with name "%s" already exist. Please choose another one.' % value)
        return value


# Import handler related forms

class BaseImportHandlerForm(BaseForm):
    def clean_data(self, value, field):
        if not value:
            return

        try:
            plan = ExtractionPlan(json.dumps(value), is_file=False)
            self.cleaned_data['import_params'] = plan.input_params
        except (ValueError, ImportHandlerException) as exc:
            raise ValidationError('Import Handler JSON file is invalid: %s' % exc)

        return value


class ImportHandlerAddForm(BaseImportHandlerForm):
    name = CharField()
    data = JsonField()
    import_params = JsonField()

    def clean_name(self, value, field):
        count = ImportHandler.query.filter_by(name=value).count()
        if count:
            raise ValidationError(
                'Import Handler with name "%s" already exist. Please choose another one.' % value)
        return value


class HandlerForm(BaseForm):
    name = CharField()


class BaseInnerDocumentForm(BaseForm):
    EXTRA_FIELDS = {}

    def __init__(self, obj, num):
        self.num = int(num)
        super(BaseInnerDocumentForm, self).__init__(
            data_from_request=False, obj=obj)

    def save(self):
        if self.num == -1:
            self.cleaned_data.update(self.EXTRA_FIELDS)
            self.obj.append(self.cleaned_data)
        else:
            for key, val in self.cleaned_data.iteritems():
                self.obj[self.num][key] = val


class HandlerDataSourceForm(BaseInnerDocumentForm):
    name = CharField()
    type_field = ChoiceField(
        choices=PredefinedDataSource.TYPES_LIST, name='type')
    db = JsonField()
    predefined_selected = BooleanField()
    datasource = DocumentField(
        doc=PredefinedDataSource, by_name=False, return_doc=True)

    def validate_data(self):
        predefined_selected = self.cleaned_data.get(
            'predefined_selected', False)
        ds = self.cleaned_data.get('datasource', None)
        if predefined_selected and ds is None:
            raise ValidationError('Predefined datasource not found')

    def save(self):
        predefined_selected = self.cleaned_data.pop(
            'predefined_selected', False)
        ds = self.cleaned_data.pop('datasource', None)
        if predefined_selected:
            self.cleaned_data = {'name': ds.name, 'type': ds.type, 'db': ds.db}
        return super(HandlerDataSourceForm, self).save()


class QueryForm(BaseInnerDocumentForm):
    EXTRA_FIELDS = {'items': []}
    name = CharField()
    sql = CharField()


class QueryItemForm(BaseInnerDocumentForm):
    EXTRA_FIELDS = {'target_features': []}
    source = CharField()
    process_as = CharField()  # TODO: choice field
    is_required = BooleanField()


class TargetFeatureForm(BaseInnerDocumentForm):
    name = CharField()
    jsonpath = CharField()
    key_path = CharField()
    value_path = CharField()
    to_csv = BooleanField()
    expression = JsonField()


# put actions forms
class ImportHandlerTestForm(BaseForm):
    params = JsonField()
    limit = IntegerField()


class QueryTestForm(BaseForm):
    sql = CharField()
    params = JsonField()
    limit = IntegerField()
    datasource = CharField()


# DataSet forms

class DataSetAddForm(BaseForm):
    required_fields = ('format', )
    format = ChoiceField(choices=DataSet.FORMATS)
    import_params = JsonField()
    handler_type = ChoiceField(choices=('XML', 'Simple'))

    def before_clean(self):
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
        from tasks import import_data

        dataset = super(DataSetAddForm, self).save(commit=False)

        str_params = "-".join(["%s=%s" % item
                              for item in dataset.import_params.iteritems()])
        dataset.name = "%s: %s" % (self.importhandler.name, str_params)
        dataset.import_handler_id = self.importhandler.id
        dataset.compress = True
        dataset.save()
        dataset.set_file_path()
        import_data.delay(str(dataset.id))
        return dataset


class DataSetEditForm(BaseForm):
    name = CharField()
