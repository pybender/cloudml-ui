from lxml import etree
from sqlalchemy.orm import relationship, deferred, backref, validates
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import undefer, joinedload_all, joinedload

from import_handlers import ImportHandlerMixin
from api.base.models import db, BaseMixin, JSONType
from core.xmlimporthandler.inputs import Input
from core.xmlimporthandler.entities import Field
from core.xmlimporthandler.datasources import DataSource


class XmlImportHandler(db.Model, ImportHandlerMixin):
    TYPE = 'xml'

    DATASOURCES_ORDER = ['db', 'csv', 'http', 'pig']

    @property
    def data(self):
        return self.get_plan_config()

    @data.setter
    def data(self, val):
        fill_import_handler(self, val)

    def _get_in_order(self, items, field, order):
        from collections import OrderedDict
        data = OrderedDict([(key, []) for key in order])
        for item in items:
            data[getattr(item, field)].append(item)
        for key in data:
            for item in data[key]:
                yield item

    def get_plan_config(self, pretty_print=True):
        plan = etree.Element("plan")

        inputs = etree.SubElement(plan, "inputs")
        for param in self.xml_input_parameters:
            etree.SubElement(inputs, "param", **param.to_dict())

        for scr in self.xml_scripts:
            scr_tag = etree.SubElement(plan, 'script')
            scr_tag.text = etree.CDATA(scr.data)

        datasources = etree.SubElement(plan, "datasources")
        for ds in self._get_in_order(self.xml_data_sources, 'type',
                                     self.DATASOURCES_ORDER):
            etree.SubElement(
                datasources, ds.type, name=ds.name, **ds.params)

        import_ = etree.SubElement(plan, "import")
        tree = get_entity_tree(self)

        def build_tree(entity, parent):
            ent = etree.SubElement(parent, "entity", **entity.to_dict())

            for sqoop in entity.sqoop_imports:
                sqoop_el = etree.SubElement(ent, "sqoop", **sqoop.to_dict())
                if sqoop.text:
                    sqoop_el.text = etree.CDATA(sqoop.text)

            if entity.query_obj:
                query = etree.SubElement(
                    ent, "query", **entity.query_obj.to_dict())
                query.text = etree.CDATA(entity.query_obj.text)

            for field in entity.fields:
                field_dict = field.to_dict()
                script = field_dict.get('script')
                script_text = None
                if script and (len(script.splitlines()) > 1
                               or len(script) > 50):
                    del field_dict['script']
                    script_text = script
                field_el = etree.SubElement(ent, "field", **field_dict)
                if script_text:
                    script_tag = etree.SubElement(field_el, "script")
                    script_tag.text = etree.CDATA(script_text)

            for subentity in entity.entities:
                build_tree(subentity, parent=ent)

        build_tree(tree, import_)

        return etree.tostring(plan, pretty_print=pretty_print)

    def get_iterator(self, params, callback=None):
        from core.xmlimporthandler.importhandler import ExtractionPlan, \
            ImportHandler as CoreImportHandler
        plan = ExtractionPlan(self.get_plan_config(), is_file=False)
        return CoreImportHandler(plan, params, callback=callback)

    def get_fields(self):
        """
        Returns list of the field names
        """
        return []

    def get_import_params(self):
        return [p.name for p in self.input_parameters]

    def update_import_params(self):
        self.import_params = [p.name for p in self.xml_input_parameters]
        self.save()

    def __repr__(self):
        return "<Import Handler %s>" % self.name


class RefXmlImportHandlerMixin(object):
    @declared_attr
    def import_handler_id(cls):
        return db.Column('import_handler_id',
                         db.ForeignKey('xml_import_handler.id'))

    @declared_attr
    def import_handler(cls):
        from api.base.utils import convert_name, pluralize
        backref_name = pluralize(convert_name(cls.__name__))
        return relationship(
            "XmlImportHandler", backref=backref(backref_name,
                                                cascade='all,delete'))


class XmlDataSource(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    TYPES = DataSource.DATASOURCE_DICT.keys()

    # TODO: unique for XmlImportHandler
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES, name='xml_datasource_types'))
    params = db.Column(JSONType)

    @validates('params')
    def validate_params(self, key, params):  # TODO:
        return params

    def __repr__(self):
        return "<DataSource %s>" % self.name


class XmlInputParameter(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    FIELDS_TO_SERIALIZE = ['name', 'type', 'regex', 'format']
    TYPES = Input.PROCESS_STRATEGIES.keys()

    # TODO: unique for XmlImportHandler
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES, name='xml_input_types'))
    regex = db.Column(db.String(200))
    format = db.Column(db.String(200))

    def save(self, *args, **kwargs):
        super(XmlInputParameter, self).save(*args, **kwargs)
        self.import_handler.update_import_params()

    def delete(self, *args, **kwargs):
        handler = self.import_handler
        super(XmlInputParameter, self).delete(*args, **kwargs)
        handler.update_import_params()


class XmlScript(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    data = db.Column(db.Text)


class XmlQuery(db.Model, BaseMixin):
    FIELDS_TO_SERIALIZE = ['target', ]
    target = db.Column(db.String(200))
    text = db.Column(db.Text)

    def __repr__(self):
        return "<Query %s>" % self.text


class XmlField(db.Model, BaseMixin):
    TYPES = Field.PROCESS_STRATEGIES.keys()
    TRANSFORM_TYPES = ['json', 'csv']
    FIELDS_TO_SERIALIZE = ['name', 'type', 'column', 'jsonpath', 'join',
                           'regex', 'split', 'dateFormat', 'template',
                           'transform', 'headers', 'script', 'required',
                           'multipart']

    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES, name='xml_field_types'))
    column = db.Column(db.String(200))
    jsonpath = db.Column(db.String(200))
    join = db.Column(db.String(200))
    regex = db.Column(db.String(200))
    split = db.Column(db.String(200))
    dateFormat = db.Column(db.String(200))
    template = db.Column(db.String(200))
    transform = db.Column(
        db.Enum(*TRANSFORM_TYPES, name='xml_transform_types'))
    headers = db.Column(db.String(200))
    script = db.Column(db.Text)
    required = db.Column(db.Boolean, default=False)
    multipart = db.Column(db.Boolean, default=False)

    entity_id = db.Column(db.ForeignKey('xml_entity.id'))
    entity = relationship(
        'XmlEntity', foreign_keys=[entity_id], backref=backref(
            'fields', cascade='all,delete', order_by='XmlField.id'))


class XmlSqoop(db.Model, BaseMixin):
    target = db.Column(db.String(200), nullable=False)
    table = db.Column(db.String(200), nullable=False)
    where = db.Column(db.String(200), nullable=True)
    direct = db.Column(db.String(200), nullable=True)
    mappers = db.Column(db.String(200), nullable=True)
    text = db.Column(db.Text, nullable=True)

    FIELDS_TO_SERIALIZE = ['target', 'table', 'where', 'direct', 'mappers']

    # Global datasource
    datasource_id = db.Column(db.ForeignKey('xml_data_source.id',
                                            ondelete='SET NULL'))
    datasource = relationship('XmlDataSource',
                              foreign_keys=[datasource_id])

    entity_id = db.Column(db.ForeignKey('xml_entity.id'))
    entity = relationship(
        'XmlEntity', foreign_keys=[entity_id], backref=backref(
            'sqoop_imports', cascade='all,delete', order_by='XmlSqoop.id'))

    def to_dict(self):
        sqoop = super(XmlSqoop, self).to_dict()
        if self.datasource:
            sqoop['datasource'] = self.datasource.name
        return sqoop


def get_entity_tree(handler):
    entity = XmlEntity.query\
        .options(
            joinedload_all('fields'),
            joinedload_all('sqoop_imports'),
            joinedload('sqoop_imports.datasource'),
            joinedload_all('entities', 'entities', 'entities'),
            joinedload('entities.sqoop_imports'),
            joinedload('entities.sqoop_imports.datasource'),
            joinedload('entities.fields'),
            joinedload('entities.entities.fields'),
            joinedload('entities.entities.entities.fields'),
            joinedload('datasource'),
            joinedload('entities.datasource'),
            joinedload('entities.transformed_field'),
            joinedload('entities.entities.datasource'),
            joinedload('entities.entities.entities.datasource'),
            joinedload('query_obj'),
            joinedload('entities.query_obj'),
            joinedload('entities.entities.query_obj'),
            joinedload('entities.entities.entities.query_obj')).filter_by(
                import_handler=handler,
                entity=None).one()
    return entity


class XmlEntity(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    # JSON or CSV field as datasource
    transformed_field_id = db.Column(db.ForeignKey(
        'xml_field.id', use_alter=True,
        name="fk_transformed_field", ondelete='SET NULL'))
    transformed_field = relationship('XmlField', post_update=True,
                                     foreign_keys=[transformed_field_id],
                                     backref='entities_for_field_ds')
    # Sub entity
    entity_id = db.Column(db.ForeignKey('xml_entity.id'))
    entity = relationship('XmlEntity', remote_side=[id],
                          backref=backref('entities', cascade='all,delete'))

    # Global datasource
    datasource_id = db.Column(db.ForeignKey('xml_data_source.id',
                                            ondelete='CASCADE'))
    datasource = relationship('XmlDataSource',
                              foreign_keys=[datasource_id])
    query_id = db.Column(db.ForeignKey('xml_query.id'))
    query_obj = relationship('XmlQuery', foreign_keys=[query_id],
                             cascade='all,delete', backref='parent_entity')

    def __repr__(self):
        return "<Entity %s>" % self.name

    def to_dict(self):
        ent = {'name': self.name}
        if self.transformed_field:
            ent['datasource'] = self.transformed_field.name
        if self.datasource:
            ent['datasource'] = self.datasource.name
        return ent


def fill_import_handler(import_handler, xml_data=None):
    plan = None
    if xml_data:
        from core.xmlimporthandler.importhandler import ExtractionPlan
        plan = ExtractionPlan(xml_data, is_file=False)

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

            for sqoop in entity.sqoop_imports:
                sqoop_obj = XmlSqoop(
                    target=sqoop.target,
                    table=sqoop.table,
                    where=sqoop.where,
                    direct=sqoop.direct,
                    mappers=sqoop.mappers,
                    text=sqoop.query,
                    datasource=ds_dict.get(sqoop.datasource_name)
                )
                db_entity.sqoop_imports.append(sqoop_obj)
                db.session.add(sqoop_obj)

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