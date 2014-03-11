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

        def build_tree(entity):
            ent = etree.SubElement(import_, "entity", **entity.to_dict())
            if entity.query_obj:
                query = etree.SubElement(
                    ent, "query", **entity.query_obj.to_dict())
                query.text = etree.CDATA(entity.query_obj.text)

            for field in entity.fields:
                etree.SubElement(ent, "field", **field.to_dict())
            for subentity in entity.entities:
                build_tree(subentity)

        for item_dict in tree.values():
            entity = item_dict['entity']
            build_tree(entity)

        return etree.tostring(plan, pretty_print=pretty_print)

    def get_iterator(self, params):
        from core.xmlimporthandler.importhandler import ExtractionPlan, \
            ImportHandler as CoreImportHandler
        plan = ExtractionPlan(self.get_plan_config(), is_file=False)
        return CoreImportHandler(plan, params)

    def get_fields(self):
        """
        Returns list of the field names
        """
        return []

    def get_import_params(self):
        return [p.name for p in self.input_parameters]


class RefXmlImportHandlerMixin(object):
    @declared_attr
    def import_handler_id(cls):
        return db.Column('import_handler_id',
                         db.ForeignKey('xml_import_handler.id'))

    @declared_attr
    def import_handler(cls):
        from api.base.utils import convert_name, pluralize
        backref = pluralize(convert_name(cls.__name__))
        return relationship(
            "XmlImportHandler", backref=backref)


class XmlDataSource(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    TYPES = DataSource.DATASOURCE_DICT.keys()

    # TODO: unique for XmlImportHandler
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES, name='xml_datasource_types'))
    params = db.Column(JSONType)

    @validates('params')
    def validate_params(self, key, params):  # TODO:
        return params


class XmlInputParameter(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    FIELDS_TO_SERIALIZE = ['name', 'type', 'regex', 'format']
    TYPES = Input.PROCESS_STRATEGIES.keys()

    # TODO: unique for XmlImportHandler
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES, name='xml_input_types'))
    regex = db.Column(db.String(200))
    format = db.Column(db.String(200))


class XmlScript(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    data = db.Column(db.Text)


class XmlQuery(db.Model, BaseMixin):
    FIELDS_TO_SERIALIZE = ['target', ]
    target = db.Column(db.String(200))
    text = db.Column(db.Text)


class XmlEntity(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    datasource_name = db.Column(db.String(200), nullable=True)
    entity_id = db.Column(db.ForeignKey('xml_entity.id',
                                        ondelete='CASCADE'))
    entity = relationship('XmlEntity', remote_side=[id], backref='entities')

    datasource_id = db.Column(db.ForeignKey('xml_data_source.id',
                                            ondelete='CASCADE'))
    datasource = relationship('XmlDataSource',
                              foreign_keys=[datasource_id])
    query_id = db.Column(db.ForeignKey('xml_query.id', ondelete='CASCADE'))
    query_obj = relationship('XmlQuery', foreign_keys=[query_id])

    def to_dict(self):
        ent = {'name': self.name, 'datasource': self.datasource_name}
        if self.datasource:
            ent['datasource'] = self.datasource.name
        return ent


class XmlField(db.Model, BaseMixin):
    TYPES = Field.PROCESS_STRATEGIES.keys()
    TRANSFORM_TYPES = ['json', 'csv']
    FIELDS_TO_SERIALIZE = ['name', 'type', 'column', 'jsonpath', 'join',
                           'regex', 'split', 'dateFormat', 'template',
                           'transform', 'headers', 'script']

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

    entity_id = db.Column(db.ForeignKey('xml_entity.id', ondelete='CASCADE'))
    entity = relationship(
        'XmlEntity', foreign_keys=[entity_id], backref='fields')


def get_entity_tree(handler):
    def load_ent(parent=None):
        return XmlEntity.query\
            .options(
                joinedload_all(XmlEntity.fields),
                joinedload(XmlEntity.datasource),
                joinedload(XmlEntity.query_obj)).filter_by(
                    import_handler=handler,
                    entity=parent)

    def new_ent(entity):
        res = {'entity': entity, 'entities': {}}
        for sub_ent in load_ent(entity):
            res['entities'][sub_ent.name] = new_ent(sub_ent)
        return res

    entity = load_ent().one()
    return {entity.name: new_ent(entity)}
