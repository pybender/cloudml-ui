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
        import_handler = XmlImportHandler(name=self.cleaned_data['name'])
        db.session.add(import_handler)

        data = self.cleaned_data.get('data')
        if data is not None:  # Loading import handler from XML file
            from core.xmlimporthandler.importhandler import ExtractionPlan
            plan = ExtractionPlan(data, is_file=False)
            for datasource in plan.datasources.values():
                ds = XmlDataSource(
                    name=datasource.name,
                    type_=datasource.type,
                    import_handler=import_handler,
                    params={})
                db.session.add(ds)

            for inp in plan.inputs.values():
                param = InputParameter(
                    name=inp.name,
                    type_=inp.type,
                    regex=inp.regex,
                    format=inp.format,
                    import_handler=import_handler)
                db.session.add(param)

            for scr in plan.data.xpath("script"):
                script = Script(
                    data=scr.text, import_handler=import_handler)
                db.session.add(script)

            entity = Entity(
                name=plan.entity.name, import_handler=import_handler)
            db.session.add(entity)

        db.session.commit()

        return import_handler
