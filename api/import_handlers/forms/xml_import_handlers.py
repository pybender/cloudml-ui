from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField, \
    DocumentField
from api.import_handlers.models import XmlImportHandler, XmlDataSource, \
    XmlInputParameter, XmlScript, XmlEntity, XmlField, XmlQuery, XmlSqoop
from api import app
from core.xmlimporthandler.exceptions import ImportHandlerException

db = app.sql_db


class XmlImportHandlerAddForm(BaseForm):
    required_fields = ('name', )

    name = CharField()
    data = CharField()

    def clean_name(self, value, field):
        count = XmlImportHandler.query.filter_by(name=value).count()
        if count:
            raise ValidationError('Import Handler with name "%s" already \
exist. Please choose another one.' % value)
        return value

    def clean_data(self, value, field):
        if value is None:
            return

        value = value.encode('utf-8')
        try:
            from core.xmlimporthandler.importhandler import ExtractionPlan
            ExtractionPlan(value, is_file=False)
            return value
        except Exception as exc:
            raise ValidationError(exc)

    def save(self):
        try:
            import_handler = XmlImportHandler(
                name=self.cleaned_data['name'],
                import_params=[])
            import_handler._set_user()
            db.session.add(import_handler)
            import_handler.data = self.cleaned_data.get('data')
        except Exception, exc:
            db.session.rollback()
            raise
        else:
            db.session.commit()

        return import_handler


class XmlImportHandlerEditForm(BaseForm):
    required_fields = ('name', )

    name = CharField()

    def clean_name(self, value, field):
        count = XmlImportHandler.query.filter_by(name=value).count()
        if count:
            raise ValidationError('Import Handler with name "%s" already \
exist. Please choose another one.' % value)
        return value


class XmlInputParameterForm(BaseForm):
    required_fields = ('name', 'type', 'import_handler_id')
    NO_REQUIRED_FOR_EDIT = True

    name = CharField()
    type_field = ChoiceField(choices=XmlInputParameter.TYPES, name='type')
    format = CharField()
    regex = CharField()
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=False)

    def clean_name(self, value, field):
        if not ((self.NO_REQUIRED_FOR_EDIT and self.obj.id) or value):
            raise ValidationError('name is required field')

        import_handler_id = self.obj.import_handler_id if \
            self.obj.id else self.data['import_handler_id']

        query = XmlInputParameter.query.filter_by(
            name=value,
            import_handler_id=import_handler_id
        )
        if self.obj.id:
            query = query.filter(XmlInputParameter.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError('Input parameter with name "%s" already \
exist. Please choose another one.' % value)
        return value


class XmlEntityForm(BaseForm):
    required_fields = ('name', 'import_handler_id',
                       'entity_id', ('datasource', 'transformed_field'))
    NO_REQUIRED_FOR_EDIT = True
    DATASOURCE_MESSAGE = 'Can be only one of either datasource or' \
                         ' transformed_field'

    name = CharField()
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=False)
    entity_id = DocumentField(
        doc=XmlEntity, by_name=False, return_doc=False)
    datasource = DocumentField(
        doc=XmlDataSource, by_name=False, return_doc=True)
    transformed_field = DocumentField(
        doc=XmlField, by_name=False, return_doc=True)

    def clean_datasource(self, value, field):
        if value and self.data.get('transformed_field'):
            raise ValidationError(self.DATASOURCE_MESSAGE)
        return value

    def clean_transformed_field(self, value, field):
        if value and self.data.get('datasource'):
            raise ValidationError(self.DATASOURCE_MESSAGE)
        return value

    def save(self, *args, **kwargs):
        try:
            entity = super(XmlEntityForm, self).save()

            if self.cleaned_data.get('transformed_field') and \
                    entity.datasource:
                entity.datasource = None
            if self.cleaned_data.get('datasource') and \
                    entity.transformed_field:
                entity.transformed_field = None
            db.session.add(entity)

            if entity.transformed_field and entity.query_obj:
                db.session.delete(entity.query_obj)
            elif entity.datasource and not entity.query_obj:
                query = XmlQuery()
                db.session.add(query)
                entity.query_obj = query
                db.session.add(entity)

            ds = entity.datasource
            if not ds or (ds and ds.type != 'pig'):
                for sqoop in entity.sqoop_imports:
                    db.session.delete(sqoop)

        except Exception:
            db.session.rollback()
            raise
        else:
            db.session.commit()

        return entity


class XmlFieldForm(BaseForm):
    required_fields = ('name', )
    NO_REQUIRED_FOR_EDIT = True

    name = CharField()
    type = ChoiceField(choices=XmlField.TYPES)
    column = CharField()
    jsonpath = CharField()
    delimiter = CharField()
    regex = CharField()
    split = CharField()
    dateFormat = CharField()
    template = CharField()
    transform = ChoiceField(choices=XmlField.TRANSFORM_TYPES)
    headers = CharField()
    script = CharField()
    required = BooleanField()
    multipart = BooleanField()
    entity_id = DocumentField(
        doc=XmlEntity, by_name=False, return_doc=False)
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=False)


def _get_ds_types():
    from core.xmlimporthandler.importhandler import ExtractionPlan
    return ExtractionPlan.get_datasources_config().keys()


class XmlDataSourceForm(BaseForm):
    required_fields = ('name', 'type', 'import_handler_id')
    NO_REQUIRED_FOR_EDIT = True

    name = CharField()
    type_field = ChoiceField(choices=_get_ds_types(), name='type')
    params = JsonField()
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=False)

    def clean_params(self, value, field):
        from core.xmlimporthandler.importhandler import ExtractionPlan
        conf = ExtractionPlan.get_datasources_config().get(
            self.data.get('type'))
        params_errors = []
        if conf:
            for param in conf:
                if param['required'] and param['name'] not in value:
                    params_errors.append(param['name'])
        if params_errors:
            raise ValidationError(
                'These params are required: {}'.format(
                    ', '.join(params_errors))
            )
        return value


class XmlQueryForm(BaseForm):
    required_fields = ('text', 'entity_id', 'import_handler_id')
    NO_REQUIRED_FOR_EDIT = True

    text = CharField()
    target = CharField()
    entity_id = DocumentField(
        doc=XmlEntity, by_name=False, return_doc=False)
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=False)


class XmlScriptForm(BaseForm):
    required_fields = ('data', 'import_handler_id')
    NO_REQUIRED_FOR_EDIT = True

    data = CharField()
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=False)


class XmlSqoopForm(BaseForm):
    required_fields = ('entity', 'target', 'table', 'datasource')
    NO_REQUIRED_FOR_EDIT = True

    MAX_ITEMS_BY_ENTITY = 3

    entity = DocumentField(
        doc=XmlEntity, by_name=False, return_doc=True)
    datasource = DocumentField(
        doc=XmlDataSource, by_name=False, return_doc=True)
    target = CharField()
    table = CharField()
    where = CharField()
    direct = CharField()
    mappers = CharField()
    text = CharField()

    def clean_entity(self, value, field):
        if value:
            if not (value.datasource and value.datasource.type == 'pig'):
                raise ValidationError('Only "pig" entity is allowed')
        if value and not self.is_edit:
            query = XmlSqoop.query.filter_by(entity=value)
            if query.count() >= self.MAX_ITEMS_BY_ENTITY:
                raise ValidationError(
                    'There can be no more than {0} elements'.format(
                        self.MAX_ITEMS_BY_ENTITY))
        return value

    def clean_datasource(self, value, field):
        if value:
            if value.type != 'db':
                raise ValidationError('Only "db" datasources are allowed')
        return value


class PredictModelForm(BaseForm):
    required_fields = ('name', ('value', 'script'), 'import_handler_id')
    NO_REQUIRED_FOR_EDIT = True

    name = CharField()
    value = CharField()
    script = CharField()
    positive_label_value = CharField()
    positive_label_script = CharField()
    import_handler_id = DocumentField(
        doc=XmlImportHandler, by_name=False, return_doc=True)

    def save(self, *args, **kwargs):
        model = super(PredictModelForm, self).save(commit=False)
        predict = self.cleaned_data['import_handler_id'].predict
        predict.models.append(model)
        predict.save()
