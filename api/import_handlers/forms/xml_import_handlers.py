from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField, \
    DocumentField
from api.import_handlers.models import XmlImportHandler, XmlDataSource, \
    XmlInputParameter, XmlScript, XmlEntity, XmlField, XmlQuery
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
            return ExtractionPlan(value, is_file=False)
        except Exception as exc:
            raise ValidationError(exc)

    def save(self):
        try:
            import_handler = XmlImportHandler(
                name=self.cleaned_data['name'],
                import_params=[])
            db.session.add(import_handler)
            plan = self.cleaned_data.get('data')
            if plan is None:
                ent = XmlEntity(
                    name=import_handler.name,
                    import_handler=import_handler)
                ent.save()
            else:  # Loading import handler from XML file
                ds_dict = {}
                for datasource in plan.datasources.values():
                    POSSIBLE_PARAMS = ['host', 'dbname', 'port',
                                       'user', 'password', 'vender']
                    ds = XmlDataSource(
                        name=datasource.name,
                        type=datasource.type,
                        import_handler=import_handler,
                        params=datasource.get_params())
                    ds_dict[datasource.name] = ds
                    db.session.add(ds)

                for inp in plan.inputs.values():
                    param = XmlInputParameter(
                        name=inp.name,
                        type=inp.type,
                        regex=inp.regex,
                        format=inp.format,
                        import_handler=import_handler)
                    db.session.add(param)
                    import_handler.import_params.append(inp.name)

                for scr in plan.data.xpath("script"):
                    script = XmlScript(
                        data=scr.text, import_handler=import_handler)
                    db.session.add(script)

                def get_datasource(entity):
                    if entity.datasource_name and \
                            entity.datasource_name in ds_dict:
                        return ds_dict[entity.datasource_name]
                    return None

                def load_query(entity, db_entity):
                    if entity.query:
                        qr = XmlQuery(
                            text=entity.query,
                            target=entity.query_target)
                        db.session.add(qr)
                        db_entity.query_obj = qr
                    return None

                TRANSFORMED_FIELDS = {}
                ENTITIES_WITHOUT_DS = []

                def load_entity_items(entity, db_entity):
                    for field in entity.fields.values():
                        fld = XmlField(
                            name=field.name,
                            type=field.type,
                            column=field.column,
                            jsonpath=field.jsonpath,
                            join=field.join,
                            regex=field.regex,
                            split=field.split,
                            dateFormat=field.dateFormat,
                            template=field.template,
                            script=field.script,
                            transform=field.transform,
                            headers=field.headers)
                        db_entity.fields.append(fld)
                        if field.transform:
                            TRANSFORMED_FIELDS[field.name] = fld
                        db.session.add(fld)

                    sub_entities = entity.nested_entities_field_ds.values() + \
                        entity.nested_entities_global_ds
                    for sub_entity in sub_entities:
                        sub_ent = XmlEntity(
                            name=sub_entity.name,
                            import_handler=import_handler)
                        sub_ent.entity = db_entity
                        sub_ent.datasource = get_datasource(sub_entity)
                        if not sub_ent.datasource:
                            ENTITIES_WITHOUT_DS.append(
                                [sub_ent, sub_entity.datasource_name])
                        db.session.add(sub_ent)
                        load_query(sub_entity, db_entity=sub_ent)
                        load_entity_items(sub_entity, db_entity=sub_ent)

                ent = XmlEntity(
                    name=plan.entity.name,
                    import_handler=import_handler,
                    datasource=get_datasource(plan.entity))
                if not ent.datasource:
                    ENTITIES_WITHOUT_DS.append(
                        [ent, plan.entity.datasource_name])
                db.session.add(ent)
                load_query(plan.entity, db_entity=ent)
                load_entity_items(plan.entity, db_entity=ent)
                for ent, field_name in ENTITIES_WITHOUT_DS:
                    ent.transformed_field = TRANSFORMED_FIELDS[field_name]

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
            entity = super(XmlEntityForm, self).save(commit=False)
            db.session.commit()

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
    join = CharField()
    regex = CharField()
    split = CharField()
    dateFormat = CharField()
    template = CharField()
    transform = ChoiceField(choices=XmlField.TRANSFORM_TYPES)
    headers = CharField()
    script = CharField()
    required = BooleanField()
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
                'These params are required: {}'.format(', '.join(params_errors))
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
