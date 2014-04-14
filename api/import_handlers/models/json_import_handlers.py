import json
import logging
import os
import StringIO
import uuid
from os.path import join, exists
from os import makedirs

from boto.exception import S3ResponseError
from sqlalchemy.orm import relationship, deferred, backref, validates

from api import app
from api.amazon_utils import AmazonS3Helper
from api.base.models import db, BaseModel, JSONType, assertion_msg
from api.logs.models import LogMessage
from import_handlers import ImportHandlerMixin


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


class ImportHandler(db.Model, ImportHandlerMixin):
    TYPE = 'json'

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

    def get_plan_config(self):
        """ Returns config that would be used for creating Extraction Plan """
        return json.dumps(self.data)

    def get_iterator(self, params):
        from core.importhandler.importhandler import ExtractionPlan, \
            ImportHandler as CoreImportHandler
        plan = ExtractionPlan(self.get_plan_config(), is_file=False)
        return CoreImportHandler(plan, params)

    def get_fields(self):
        from core.importhandler.importhandler import ExtractionPlan
        if self.data is None:
            return []
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
