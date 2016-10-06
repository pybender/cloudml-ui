"""
Import handler related models declared here.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
from lxml import etree
from sqlalchemy.orm import relationship, deferred, backref, validates
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import undefer, joinedload_all, joinedload
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event

from api.base.models import db, BaseMixin, JSONType
from cloudml.importhandler.datasources import DbDataSource
from cloudml.importhandler.inputs import Input
from cloudml.importhandler.scripts import Script
from cloudml.importhandler.entities import Field
from cloudml.importhandler.datasources import DataSource
from cloudml.importhandler.importhandler import ExtractionPlan, \
    ImportHandler as CoreImportHandler
from cloudml.importhandler.utils import PROCESS_STRATEGIES
from api.base.models import db, BaseModel
from api.base.models.models import BaseDeployedEntity
from api import app
from api.base.exceptions import ApiBaseException


class XMLScriptError(ApiBaseException):
    pass


class ImportHandlerError(ApiBaseException):
    pass

class ImportHandlerMixin(BaseModel):
    """
    Base class for any import handler.
    """
    TYPE = 'N/A'

    @property
    def type(self):
        return self.TYPE

    @property
    def identifier(self):
        return "{0}{1}".format(self.id, self.TYPE)

    @declared_attr
    def name(cls):
        return db.Column(db.String(200), nullable=False, unique=True)

    @declared_attr
    def import_params(cls):
        return db.Column(postgresql.ARRAY(db.String))

    def get_plan_config(self):
        """ Returns config that would be used for creating Extraction Plan """
        return ""

    def get_iterator(self, params):
        raise Exception('not inplemented')

    def get_fields(self):
        """
        Returns list of the field names
        """
        return []

    def create_dataset(self, params, data_format='json', compress=True):
        from datasets import DataSet
        dataset = DataSet()
        str_params = "-".join(["%s=%s" % item
                               for item in params.iteritems()])
        dataset.name = ("%s: %s" % (self.name, str_params))[:199]
        dataset.import_handler_id = self.id
        dataset.import_handler_type = self.TYPE
        dataset.import_handler_xml = self.data
        dataset.import_params = params
        dataset.format = data_format
        dataset.compress = compress
        dataset.save()
        dataset.set_file_path()
        return dataset

    def check_sql(self, sql):
        """
        Parses sql query structure from text,
        raises Exception if it's not a SELECT query or invalid sql.
        """
        import sqlparse

        query = sqlparse.parse(sql)
        error_msg = None
        if len(query) < 1:
            error_msg = 'Unable to detect a query in the supplied text'
        else:
            query = query[0]
            if query.get_type() != 'SELECT':
                error_msg = 'Only supporting SELECT queries'

        if error_msg is not None:
            raise Exception(error_msg)
        else:
            return query

    def build_query(self, sql, limit=2):
        """
        Parses sql query and changes LIMIT statement value.
        """
        import re
        from sqlparse import parse, tokens
        from sqlparse.sql import Token

        # It's important to have a whitespace right after every LIMIT
        pattern = re.compile('limit([^ ])', re.IGNORECASE)
        sql = pattern.sub(r'LIMIT \1', sql)

        query = parse(sql.rstrip(';'))[0]

        # Find LIMIT statement
        token = query.token_next_match(0, tokens.Keyword, 'LIMIT')
        if token:
            # Find and replace LIMIT value
            value = query.token_next(query.token_index(token), skip_ws=True)
            if value:
                new_token = Token(value.ttype, str(limit))
                query.tokens[query.token_index(value)] = new_token
        else:
            # If limit is not found, append one
            new_tokens = [
                Token(tokens.Whitespace, ' '),
                Token(tokens.Keyword, 'LIMIT'),
                Token(tokens.Whitespace, ' '),
                Token(tokens.Number, str(limit)),
            ]
            last_token = query.tokens[-1]
            if last_token.ttype == tokens.Punctuation:
                query.tokens.remove(last_token)
            for new_token in new_tokens:
                query.tokens.append(new_token)

        return str(query)

    def execute_sql_iter(self, sql, datasource_name):
        """
        Executes sql using data source with name datasource_name.
        Datasource with given name should be in handler's datasource list.
        Returns iterator.
        """
        vendor, conn = self._get_ds_details_for_query(datasource_name)
        iter_func = DbDataSource.DB.get(vendor)[0]

        for row in iter_func([sql], conn):
            yield dict(row)

    def _get_ds_details_for_query(self, ds_name):
        raise NotImplementedError()

    def __repr__(self):
        return '<%s Import Handler %r>' % (self.TYPE, self.name)


class XmlImportHandler(db.Model, ImportHandlerMixin, BaseDeployedEntity):
    TYPE = 'xml'

    DATASOURCES_ORDER = ['db', 'csv', 'http', 'pig', 'input']

    predict_id = db.Column(db.ForeignKey('predict.id', ondelete='CASCADE'))
    predict = relationship(
        'Predict', foreign_keys=[predict_id], backref="import_handler")
    locked = db.Column(db.Boolean, default=False)

    @property
    def data(self):
        return self.get_plan_config()

    @property
    def crc32(self):
        import zlib
        return '0x%08X' % (zlib.crc32(self.data) & 0xffffffff)

    @data.setter
    def data(self, val):
        has_root_ent = XmlEntity.query.filter_by(
            import_handler=self,
            entity=None).count()
        if has_root_ent:
            raise ValueError("Import Handler isn't empty")

        fill_import_handler(self, val)

    def _get_in_order(self, items, field, order):
        from collections import OrderedDict
        data = OrderedDict([(key, []) for key in order])
        for item in items:
            data[getattr(item, field)].append(item)
        for key in data:
            for item in data[key]:
                yield item

    def get_plan_config(self, pretty_print=True, secure=True):
        plan = etree.Element("plan")

        inputs = etree.SubElement(plan, "inputs")
        for param in self.xml_input_parameters:
            etree.SubElement(inputs, "param", **param.to_dict())

        for scr in self.xml_scripts:
            if scr.data and scr.data.strip():  # script isn't empty
                if scr.type == XmlScript.TYPE_PYTHON_FILE:
                    scr_tag = etree.SubElement(plan, 'script', src=scr.data)
                if scr.type == XmlScript.TYPE_PYTHON_CODE:
                    scr_tag = etree.SubElement(plan, 'script')
                    scr_tag.text = etree.CDATA(scr.data)

        datasources = etree.SubElement(plan, "datasources")
        for ds in self._get_in_order(self.xml_data_sources, 'type',
                                     self.DATASOURCES_ORDER):
            if ds.name != "input":
                extra = ds.params if secure else {}
                etree.SubElement(
                    datasources, ds.type, name=ds.name, **extra)

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
                query.text = etree.CDATA(entity.query_obj.text or '')

            for field in entity.fields:
                field_dict = field.to_dict()
                script = field_dict.get('script')
                script_text = None
                if script and (len(script.splitlines()) > 1 or
                               len(script) > 50):
                    del field_dict['script']
                    script_text = script
                field_el = etree.SubElement(ent, "field", **field_dict)
                if script_text:
                    script_tag = etree.SubElement(field_el, "script")
                    script_tag.text = etree.CDATA(script_text)

            for subentity in entity.entities:
                build_tree(subentity, parent=ent)

        build_tree(tree, import_)

        if self.predict is not None:
            predict = etree.SubElement(plan, "predict")
            for model in self.predict.models:
                predict_model = etree.SubElement(
                    predict, "model", **model.to_dict())
                for weight in model.predict_model_weights:
                    etree.SubElement(
                        predict_model, "weight", **weight.to_dict())

            if self.predict.label or self.predict.probability:
                result = etree.SubElement(predict, "result")
                etree.SubElement(
                    result, "label", **self.predict.label.to_dict())
                etree.SubElement(
                    result, "probability",
                    **self.predict.probability.to_dict())

        return etree.tostring(plan, pretty_print=pretty_print)

    def get_iterator(self, params, callback=None):
        plan = ExtractionPlan(self.get_plan_config(), is_file=False)
        return CoreImportHandler(plan, params, callback=callback)

    def get_fields(self):
        """
        Returns list of the field names
        """
        if self.data is None:
            return []

        def get_entity_fields(entity):
            fields = []
            for name, field in entity.fields.iteritems():
                if not field.is_datasource_field:
                    fields.append(field.name)
            for sub_entity in entity.nested_entities_field_ds.values():
                fields += get_entity_fields(sub_entity)
            for sub_entity in entity.nested_entities_global_ds:
                fields += get_entity_fields(sub_entity)
            return fields

        # TODO: try .. except after check this with real import handlers
        try:
            plan = ExtractionPlan(self.data, is_file=False)
            return get_entity_fields(plan.entity)
        except Exception, exc:
            logging.error(exc)
            raise ImportHandlerError(exc.message, exc)

    def list_fields(self):
        # we should have the ih saved to db to get its fields
        assert self.id > 0

        return XmlField.query.join(
            XmlEntity, XmlField.entity_id == XmlEntity.id).join(
                XmlImportHandler,
                XmlEntity.import_handler_id == XmlImportHandler.id).filter(
                    XmlImportHandler.id == self.id).all()

    # TODO: looks like obsolete
    # def get_import_params(self):
    #     return [p.name for p in self.input_parameters]

    def update_import_params(self):
        self.import_params = [p.name for p in self.xml_input_parameters]
        self.save()

    def _get_ds_details_for_query(self, ds_name):
        """
        from a dataset name returns vendor and connection string
        :param ds_name:
        :return: tuple (vendor, connection string)
        """
        ds = next((d for d in self.xml_data_sources if d.name == ds_name))
        conn = "host='{host:s}' dbname='{dbname:s}' user='{user:s}' " \
               "password='{password:s}'".format(**ds.params)
        if 'port' in ds.params:
            conn += " port={port:s}".format(**ds.params)
        return ds.params['vendor'], conn

    def __repr__(self):
        return "<Import Handler %s>" % self.name

    def _check_deployed(self):
        if not app.config['MODIFY_DEPLOYED_IH'] and self.locked:
            self.reason_msg = "Import handler {0} has been deployed and " \
                              "blocked for modifications. ".format(self.name)
            return False
        return True
    
    def _check_status_deployed(self):
        permission = app.config['MODIFY_DEPLOYED']
        canedit = True
        candelete = True
        if app.config['MODIFY_DEPLOYED_IH']:
            return (canedit, candelete)
        if not self.locked:
            return (canedit, candelete)
        try:
            for srv in self.servers:
                canedit = canedit and permission[srv.type][0]
                candelete = candelete and permission[srv.type][0]
        except:
            canedit = False
            candelete = False

        if (not canedit or not candelete):
            self.reason_msg = "Import handler {0} has been deployed and " \
                              "blocked for modifications. ".format(self.name)
            
        return (canedit, candelete)

    @property
    def can_edit(self):
        return self._check_status_deployed()[0] and super(
            XmlImportHandler, self).can_edit
    @property
    def can_delete(self):
        return self._check_status_deployed()[1] and super(
            XmlImportHandler, self).can_delete

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
    params = deferred(db.Column(JSONType))

    @validates('params')
    def validate_params(self, key, params):  # TODO:
        return params

    def to_xml(self, secure=False, to_string=False, pretty_print=True):
        extra = self.params if secure else {}
        elem = etree.Element(self.type, name=self.name, **extra)
        if to_string:
            return etree.tostring(elem, pretty_print=pretty_print)
        return elem

    @property
    def core_datasource(self):
        # TODO: secure
        ds_xml = self.to_xml(secure=True)
        return DataSource.factory(ds_xml)

    def __repr__(self):
        return "<DataSource %s>" % self.name


class XmlInputParameter(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    FIELDS_TO_SERIALIZE = ['name', 'type', 'regex', 'format']
    TYPES = PROCESS_STRATEGIES.keys()

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
    TYPE_PYTHON_CODE = 'python_code'
    TYPE_PYTHON_FILE = 'python_file'
    TYPES = [TYPE_PYTHON_CODE, TYPE_PYTHON_FILE]
    data = db.Column(db.Text)
    type = db.Column(db.Enum(*TYPES, name='xml_script_types'),
                     server_default=TYPE_PYTHON_CODE)

    @staticmethod
    def to_s3(data, import_handler_id):
        from api.amazon_utils import AmazonS3Helper
        from datetime import datetime
        import api
        try:
            handler = XmlImportHandler.query.get(import_handler_id)
            if not handler:
                raise ValueError("Import handler {0} not found".format(
                    import_handler_id))
            key = "{0}/{1}_python_script_{2}.py".format(
                api.app.config['IMPORT_HANDLER_SCRIPTS_FOLDER'],
                handler.name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            s3helper = AmazonS3Helper()
            s3helper.save_key_string(key, data)
        except Exception as e:
            raise ValueError("Error when uploading file to Amazon S3: "
                             "{0}".format(e))
        return key

    def to_xml(self, to_string=False, pretty_print=True):
        attrib = {"src": self.data} \
            if self.type == XmlScript.TYPE_PYTHON_FILE \
            else {}
        text = self.data if self.type == XmlScript.TYPE_PYTHON_CODE else None
        elem = etree.Element(self.type, attrib)
        elem.text = text
        if to_string:
            return etree.tostring(elem, pretty_print=pretty_print)
        return elem

    @property
    def script_string(self):
        try:
            script = Script(self.to_xml())
            return script.get_script_str()
        except Exception as e:
            raise ValueError("Can't load script sources. {0}".format(e))


class XmlQuery(db.Model, BaseMixin):
    FIELDS_TO_SERIALIZE = ['target', 'sqoop_dataset_name',
                           'autoload_sqoop_dataset']
    target = db.Column(db.String(200))

    # Could be filled when entity contains sqoop element
    sqoop_dataset_name = db.Column(db.String(200))
    autoload_sqoop_dataset = db.Column(db.Boolean)

    text = db.Column(db.Text)

    def __repr__(self):
        return "<Query %s>" % self.text


class XmlField(db.Model, BaseMixin):
    TYPES = PROCESS_STRATEGIES.keys()
    TRANSFORM_TYPES = ['json', 'csv']
    FIELDS_TO_SERIALIZE = ['name', 'type', 'column', 'jsonpath', 'delimiter',
                           'regex', 'split', 'dateFormat', 'template',
                           'transform', 'headers', 'script', 'required',
                           'multipart', 'key_path', 'value_path']

    def to_dict(self):
        fieldDict = super(XmlField, self).to_dict()
        if 'multipart' in fieldDict and fieldDict['multipart'] == 'false':
            fieldDict.pop('multipart')
        if 'required' in fieldDict and fieldDict['required'] == 'false':
            fieldDict.pop('required')
        return fieldDict

    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES, name='xml_field_types'))
    column = db.Column(db.String(200))
    jsonpath = db.Column(db.String(200))
    delimiter = db.Column(db.String(200))
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
    key_path = db.Column(db.String(200))
    value_path = db.Column(db.String(200))

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
    options = db.Column(db.String(200), nullable=True)
    text = db.Column(db.Text, nullable=True)

    FIELDS_TO_SERIALIZE = ['target', 'table', 'where', 'direct',
                           'mappers', 'options']

    # Global datasource
    datasource_id = db.Column(db.ForeignKey('xml_data_source.id',
                                            ondelete='SET NULL'))
    datasource = relationship('XmlDataSource',
                              foreign_keys=[datasource_id])

    entity_id = db.Column(db.ForeignKey('xml_entity.id'))
    entity = relationship(
        'XmlEntity', foreign_keys=[entity_id], backref=backref(
            'sqoop_imports', cascade='all,delete', order_by='XmlSqoop.id'))

    @property
    def pig_fields(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.import_handlers.tasks.load_pig_fields',
        )

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
    autoload_fields = db.Column(db.Boolean, default=False)

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
        if self.autoload_fields:
            ent['autoload_fields'] = str(self.autoload_fields).lower()
        return ent


# Predict section

class Predict(db.Model, BaseMixin):
    models = relationship(
        'PredictModel',
        secondary=lambda: predict_models_table, backref='predict_section')

    # Results
    label_id = db.Column(db.ForeignKey('predict_result_label.id'))
    label = relationship('PredictResultLabel', foreign_keys=[label_id],
                         cascade='all,delete', backref='results')

    probability_id = db.Column(db.ForeignKey('predict_result_probability.id'))
    probability = relationship(
        'PredictResultProbability', foreign_keys=[probability_id],
        cascade='all,delete', backref='probabilities')


class PredictModel(db.Model, BaseMixin):
    FIELDS_TO_SERIALIZE = ('name', 'value', 'script')

    name = db.Column(db.String(200), nullable=False, name='name')
    value = db.Column(db.String(200), name='value')
    script = db.Column(db.Text, name='script')

predict_models_table = db.Table(
    'predict_models_table', db.Model.metadata,
    db.Column('predict_model_id', db.Integer, db.ForeignKey(
        'predict_model.id', ondelete='CASCADE', onupdate='CASCADE')),
    db.Column('predict_id', db.Integer, db.ForeignKey(
        'predict.id', ondelete='CASCADE', onupdate='CASCADE'))
)


class RefPredictModelMixin(BaseMixin):
    @declared_attr
    def predict_model_id(cls):
        return db.Column(
            'predict_model_id', db.ForeignKey('predict_model.id'))

    @declared_attr
    def predict_model(cls):
        from api.base.utils import convert_name, pluralize
        backref_name = pluralize(convert_name(cls.__name__))
        return relationship(
            "PredictModel",
            backref=backref(backref_name))

    def to_dict(self):
        res = super(RefPredictModelMixin, self).to_dict()
        if 'predict_model' in res:
            del res['predict_model']
            res['model'] = self.predict_model.name
        return res


class PredictModelWeight(db.Model, RefPredictModelMixin):
    FIELDS_TO_SERIALIZE = ('label', 'value', 'script')

    value = db.Column(db.String(200), name='value')
    script = db.Column(db.Text, name='script')
    label = db.Column(db.String(200))


# Predict Result

class PredictResultLabel(db.Model, RefPredictModelMixin):
    FIELDS_TO_SERIALIZE = ('script', 'predict_model')

    script = db.Column(db.Text)


class PredictResultProbability(db.Model, RefPredictModelMixin):
    FIELDS_TO_SERIALIZE = ('label', 'script', 'predict_model')

    script = db.Column(db.Text)
    label = db.Column(db.String(200))


def fill_import_handler(import_handler, xml_data=None):
    plan = None
    if xml_data:
        plan = ExtractionPlan(xml_data, is_file=False)

    if plan is None:
        ent = XmlEntity(
            name=import_handler.name,
            import_handler=import_handler)
        ent.save()
    else:  # Loading import handler from XML file
        ds_dict = {}
        for datasource in plan.datasources.values():
            # if datasource.name == 'input':
            #      continue
            POSSIBLE_PARAMS = ['host', 'dbname', 'port',
                               'user', 'password', 'vender']
            ds = XmlDataSource(
                name=datasource.name,
                type=datasource.type,
                import_handler=import_handler,
                params=datasource.get_params())
            ds_dict[datasource.name] = ds
            db.session.add(ds)

        import_handler.import_params = []
        for inp in plan.inputs.values():
            param = XmlInputParameter(
                name=inp.name,
                type=inp.type,
                regex=inp.regex,
                format=inp.format,
                import_handler=import_handler)
            db.session.add(param)
            import_handler.import_params.append(inp.name)

        for scr in plan.scripts:
            script = XmlScript(
                data=scr.src or scr.text,
                type=XmlScript.TYPE_PYTHON_FILE if scr.src else
                XmlScript.TYPE_PYTHON_CODE,
                import_handler=import_handler)
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
                if hasattr(field, 'delimiter'):
                    delimiter = field.delimiter
                else:
                    delimiter = field.join
                fld = XmlField(
                    name=field.name,
                    type=field.type,
                    column=field.column,
                    jsonpath=field.jsonpath,
                    delimiter=delimiter,
                    regex=field.regex,
                    split=field.split,
                    dateFormat=field.dateFormat,
                    template=field.template,
                    script=field.script,
                    transform=field.transform,
                    headers=field.headers,
                    required=field.required,
                    multipart=field.multipart,
                    key_path=field.key_path,
                    value_path=field.value_path)
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
                    options=sqoop.options,
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
            if field_name not in TRANSFORMED_FIELDS:
                raise ValueError(
                    'Transformed field or datasource "{0}" '
                    'not found in the entity "{1}"'.format(
                        field_name, ent.name))
            ent.transformed_field = TRANSFORMED_FIELDS[field_name]

        # Fill predict section
        if plan.predict is not None:
            models_dict = {}
            predict = Predict()
            for model in plan.predict.models:
                predict_model = PredictModel(
                    name=model.name,
                    value=model.value,
                    script=model.script)
                db.session.add(predict_model)

                for weight in model.weights:
                    model_weight = PredictModelWeight(
                        label=weight.label,
                        script=weight.script,
                        value=str(weight.value or ''),
                        predict_model=predict_model)
                    db.session.add(model_weight)

                predict.models.append(predict_model)
                models_dict[model.name] = predict_model

            config_label = plan.predict.result.label
            predict.label = PredictResultLabel(
                script=config_label.script,
                predict_model=models_dict.get(config_label.model, None))

            config_probability = plan.predict.result.probability
            predict.probability = PredictResultProbability(
                script=config_probability.script,
                label=config_probability.label,
                predict_model=models_dict.get(config_probability.model, None))

            db.session.add(predict)
            import_handler.predict = predict


@event.listens_for(XmlImportHandler, "after_insert")
def create_predict(mapper, connection, target):
    """
    Creates predict section, if them doesn't exist.
    """
    if target.predict is None:
        target.predict = Predict()


@event.listens_for(Predict, "after_insert")
def create_predict(mapper, connection, target):
    """
    Creates predict section, if them doesn't exist.
    """
    if target.label is None:
        target.label = PredictResultLabel()
    if target.probability is None:
        target.probability = PredictResultProbability()
