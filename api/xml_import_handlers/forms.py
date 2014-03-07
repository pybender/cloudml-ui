from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError, BooleanField, IntegerField, \
    DocumentField
from models import XmlImportHandler, XmlDataSource, InputParameter, Script, \
    Entity, Field, Query
from api import app

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

    def save(self):
        try:
            import_handler = XmlImportHandler(name=self.cleaned_data['name'])
            db.session.add(import_handler)

            data = self.cleaned_data.get('data')
            if data is not None:  # Loading import handler from XML file
                from core.xmlimporthandler.importhandler import ExtractionPlan
                plan = ExtractionPlan(data, is_file=False)
                ds_dict = {}
                for datasource in plan.datasources.values():
                    ds = XmlDataSource(
                        name=datasource.name,
                        type=datasource.type,
                        import_handler=import_handler,
                        params={})
                    ds_dict[datasource.name] = ds
                    db.session.add(ds)

                for inp in plan.inputs.values():
                    param = InputParameter(
                        name=inp.name,
                        type=inp.type,
                        regex=inp.regex,
                        format=inp.format,
                        import_handler=import_handler)
                    db.session.add(param)

                for scr in plan.data.xpath("script"):
                    script = Script(
                        data=scr.text, import_handler=import_handler)
                    db.session.add(script)

                def get_datasource(entity):
                    if entity.datasource_name and \
                            entity.datasource_name in ds_dict:
                        return ds_dict[entity.datasource_name]
                    return None

                def load_query(entity, db_entity):
                    if entity.query:
                        qr = Query(
                            text=entity.query,
                            target=entity.query_target)
                        db.session.add(qr)
                        db_entity.query = qr
                    return None

                def load_entity_items(entity, db_entity):
                    for field in entity.fields.values():
                        fld = Field(
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
                            headers=field.headers,
                            entity=db_entity)
                        db.session.add(fld)

                    sub_entities = entity.nested_entities_field_ds.values() + \
                        entity.nested_entities_global_ds
                    for sub_entity in sub_entities:
                        sub_ent = Entity(
                            name=sub_entity.name,
                            import_handler=import_handler)
                        sub_ent.entity = db_entity
                        sub_ent.datasource = get_datasource(sub_entity)
                        db.session.add(sub_ent)
                        load_query(sub_entity, db_entity=sub_ent)
                        load_entity_items(sub_entity, db_entity=sub_ent)

                ent = Entity(
                    name=plan.entity.name,
                    import_handler=import_handler,
                    datasource=get_datasource(plan.entity))
                db.session.add(ent)
                load_query(plan.entity, db_entity=ent)
                load_entity_items(plan.entity, db_entity=ent)
        except Exception, exc:
            db.session.rollback()
            raise
        else:
            db.session.commit()

        return import_handler
