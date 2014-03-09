import json
import logging
import os
import StringIO
import uuid
from os.path import join, exists
from os import makedirs

from boto.exception import S3ResponseError
from sqlalchemy.orm import relationship, deferred, backref, validates
from sqlalchemy.dialects import postgresql

from api import app
from api.amazon_utils import AmazonS3Helper
from api.base.models import db, BaseModel, JSONType, assertion_msg
from api.logs.models import LogMessage


class PredefinedDataSource(db.Model, BaseModel):
    TYPE_REQUEST = 'http'
    TYPE_SQL = 'sql'
    TYPES_LIST = (TYPE_REQUEST, TYPE_SQL)

    VENDOR_POSTGRES = 'postgres'
    VENDORS_LIST = (VENDOR_POSTGRES, )

    name = db.Column(db.String(200), nullable=False, unique=True)
    type = db.Column(db.Enum(*TYPES_LIST, name='datasource_types'),
                     default=TYPE_SQL)
    # sample: {"conn": basestring, "vendor": basestring}
    db = deferred(db.Column(JSONType))

    @validates('db')
    def validate_db(self, key, db):
        self.validate_db_fields(db)
        return db

    @classmethod
    def validate_db_fields(cls, db):
        key = 'db'
        assert 'vendor' in db, assertion_msg(key, 'vendor is required')
        assert db['vendor'] in cls.VENDORS_LIST, assertion_msg(
            key, 'choose vendor from %s' % ', '.join(cls.VENDORS_LIST))
        assert 'conn' in db, assertion_msg(key, 'conn is required')


class ImportHandler(db.Model, BaseModel):
    name = db.Column(db.String(200), nullable=False, unique=True)
    import_params = db.Column(postgresql.ARRAY(db.String))

    data = db.Column(JSONType)

    @validates('data')
    def validate_data(self, key, data):
        assert 'target_schema' in data, assertion_msg(
            key, 'target_schema is required')

        assert 'datasource' in data, assertion_msg(
            key, 'datasource is required')
        for datasource in data['datasource']:
            assert datasource['type'] in PredefinedDataSource.TYPES_LIST, \
                assertion_msg(key, 'datasource type is invalid')
            PredefinedDataSource.validate_db_fields(datasource['db'])

        assert 'queries' in data, assertion_msg(
            key, 'queries is required')
        for query in data['queries']:
            assert "name" in query and query['name'], \
                assertion_msg(key, 'query name is required')
            assert "sql" in query and query['sql'], \
                assertion_msg(key, 'query sql is required')
            assert "items" in query and query['items'] is not None, \
                assertion_msg(key, 'query items are required')

            # TODO: If query contains items, validate them
        return data

    def get_fields(self):
        from core.importhandler.importhandler import ExtractionPlan

        data = json.dumps(self.data)
        plan = ExtractionPlan(data, is_file=False)
        test_handler_fields = []
        for query in plan.queries:
            items = query['items']
            for item in items:
                features = item['target_features']
                for feature in features:
                    test_handler_fields.append(
                        feature['name'].replace('.', '->'))
        return test_handler_fields

    def create_dataset(self, params, run_import_data=True, data_format='json'):
        dataset = DataSet()
        str_params = "-".join(["%s=%s" % item
                               for item in params.iteritems()])
        dataset.name = "%s: %s" % (self.name, str_params)
        dataset.import_handler_id = self.id
        dataset.import_params = params
        dataset.format = data_format
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
        wrong_sql = False
        if len(query) < 1:
            wrong_sql = True
        else:
            query = query[0]
            if query.get_type() != 'SELECT':
                wrong_sql = True

        if wrong_sql:
            raise Exception('Invalid sql query')
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
        from core.importhandler import importhandler
        datasource = next((d for d in self.data['datasource']
                           if d['name'] == datasource_name))

        iter_func = importhandler.ImportHandler.DB_ITERS.get(
            datasource['db']['vendor'])

        for row in iter_func([sql], datasource['db']['conn']):
            yield dict(row)

    def __repr__(self):
        return '<Import Handler %r>' % self.name


# TODO: move it xml_import_handlers

class XmlImportHandler(db.Model, BaseModel):
    name = db.Column(db.String(200), nullable=False, unique=True)

    def to_xml(self):
        from lxml import etree
        plan = etree.Element("plan")

        for scr in self.scripts:
            scr_tag = etree.SubElement(plan, 'script')
            scr_tag.text = scr.data

        inputs = etree.SubElement(plan, "inputs")
        for param in self.input_parameters:
            etree.SubElement(inputs, "param", **param.to_dict())

        datasources = etree.SubElement(plan, "datasources")
        for ds in self.xml_data_sources:
            etree.SubElement(
                datasources, ds.type, name=ds.name, **ds.params)

        import_ = etree.SubElement(plan, "import")
        from api.xml_import_handlers.models import get_entity_tree
        tree = get_entity_tree(self)

        def build_tree(entity):
            ent = etree.SubElement(import_, "entity", **entity.to_dict())
            if entity.query_obj:
                query = etree.SubElement(
                    ent, "query", **entity.query_obj.to_dict())
                query.text = entity.query_obj.text

            for field in entity.fields:
                etree.SubElement(ent, "field", **field.to_dict())
            for subentity in entity.entities:
                build_tree(subentity)

        for item_dict in tree.values():
            entity = item_dict['entity']
            build_tree(entity)

        return etree.tostring(plan, pretty_print=True)

    @property
    def import_params(self):
        return [p.name for p in self.input_parameters]


class DataSet(db.Model, BaseModel):
    LOG_TYPE = LogMessage.IMPORT_DATA

    STATUS_IMPORTING = 'Importing'
    STATUS_UPLOADING = 'Uploading'
    STATUS_IMPORTED = 'Imported'
    STATUS_ERROR = 'Error'
    STATUSES = [STATUS_IMPORTING, STATUS_UPLOADING, STATUS_IMPORTED,
                STATUS_ERROR]

    FORMAT_JSON = 'json'
    FORMAT_CSV = 'csv'
    FORMATS = [FORMAT_JSON, FORMAT_CSV]

    name = db.Column(db.String(200))
    status = db.Column(db.Enum(*STATUSES, name='dataset_statuses'))
    error = db.Column(db.String(300))  # TODO: trunc error to 300 symbols
    data = db.Column(db.String(200))
    import_params = db.Column(JSONType)

    # We will delete old IH in the future
    import_handler_id = db.Column(db.Integer,
                                  db.ForeignKey('import_handler.id'))
    import_handler = relationship('ImportHandler', backref=backref(
        'datasets', cascade='all,delete'))

    xml_import_handler_id = db.Column(
        db.Integer, db.ForeignKey('xml_import_handler.id'))
    xml_import_handler = relationship('XmlImportHandler', backref=backref(
        'datasets', cascade='all,delete'))

    on_s3 = db.Column(db.Boolean)
    compress = db.Column(db.Boolean)
    filename = db.Column(db.String(200))
    filesize = db.Column(db.BigInteger)
    records_count = db.Column(db.Integer)
    time = db.Column(db.Integer)
    data_fields = db.Column(postgresql.ARRAY(db.String))
    format = db.Column(db.String(10))
    uid = db.Column(db.String(200))

    def set_uid(self):
        if not self.uid:
            self.uid = uuid.uuid1().hex

    def get_s3_download_url(self, expires_in=3600):
        helper = AmazonS3Helper()
        return helper.get_download_url(self.uid, expires_in)

    def set_file_path(self):
        self.set_uid()
        data = '%s.%s' % (self.uid, 'gz' if self.compress else 'json')
        self.data = data
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        self.filename = join(path, data)
        self.save()

    @property
    def loaded_data(self):
        if not self.on_s3:
            raise Exception('Invalid oper')

        if not hasattr(self, '_data'):
            self._data = self.load_from_s3()
        return self._data

    def get_data_stream(self):
        import gzip
        #import zlib
        if not self.on_s3 or exists(self.filename):
            logging.info('Loading data from local file')
            open_meth = gzip.open if self.compress else open
            return open_meth(self.filename, 'r')
        else:
            logging.info('Loading data from Amazon S3')
            stream = StringIO.StringIO(self.loaded_data)
            if self.compress:
                logging.info('Decompress data')
                return gzip.GzipFile(fileobj=stream, mode='r')
                #data = zlib.decompress(data)
            return stream

    def get_iterator(self, stream):
        from core.trainer.streamutils import streamingiterload

        return streamingiterload(stream, source_format=self.format)

    def load_from_s3(self):
        helper = AmazonS3Helper()
        return helper.load_key(self.uid)

    def save_to_s3(self):
        meta = {'handler': self.import_handler_id,
                'dataset': self.name,
                'params': str(self.import_params)}
        self.set_uid()
        helper = AmazonS3Helper()
        helper.save_gz_file(self.uid, self.filename, meta)
        helper.close()
        self.on_s3 = True
        self.save()

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def delete(self):
        # Stop task
        # self.terminate_task()  # TODO
        filename = self.filename
        on_s3 = self.on_s3

        super(DataSet, self).delete()
        LogMessage.delete_related_logs(self)

        # TODO: check import handler type
        try:
            os.remove(filename)
        except OSError:
            pass
        if on_s3:
            from api.amazon_utils import AmazonS3Helper
            helper = AmazonS3Helper()
            try:
                helper.delete_key(self.uid)
            except S3ResponseError as e:
                logging.exception(str(e))

    def save(self, *args, **kwargs):
        if self.status != self.STATUS_ERROR:
            self.error = ''
        super(DataSet, self).save(*args, **kwargs)

    def __repr__(self):
        return '<Dataset %r>' % self.name
