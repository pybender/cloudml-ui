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
from sqlalchemy.ext.declarative import declared_attr

from api import app
from api.amazon_utils import AmazonS3Helper
from api.base.models import db, BaseModel, JSONType, assertion_msg, BaseMixin
from api.logs.models import LogMessage
from core.xmlimporthandler.inputs import Input
from core.xmlimporthandler.entities import Field
from core.xmlimporthandler.datasources import DataSource


class XmlImportHandler(db.Model, BaseModel):
    name = db.Column(db.String(200), nullable=False, unique=True)


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
    type_ = db.Column(db.Enum(*TYPES, name='xml_datasource_types'))
    params = db.Column(JSONType)

    @validates('params')
    def validate_params(self, key, params):  # TODO:
        return params


class InputParameter(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    TYPES = Input.PROCESS_STRATEGIES.keys()

    # TODO: unique for XmlImportHandler
    name = db.Column(db.String(200), nullable=False)
    type_ = db.Column(db.Enum(*TYPES, name='xml_input_types'))
    regex = db.Column(db.String(200))
    format = db.Column(db.String(200))


class Script(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    data = db.Column(db.String(200))


class Query(db.Model, BaseMixin):
    target = db.Column(db.String(200))
    text = deferred(db.Column(db.Text))
    entity_id = db.Column(db.ForeignKey('entity.id', ondelete='CASCADE'))
    entity = relationship('Entity', foreign_keys=[entity_id])


class Entity(db.Model, BaseMixin, RefXmlImportHandlerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    entity_id = db.Column(db.ForeignKey('entity.id',
                                        ondelete='CASCADE'))
    entity = relationship('Entity', remote_side=[id], backref='entities')

    datasource_id = db.Column(db.ForeignKey('xml_data_source.id',
                                            ondelete='CASCADE'))
    datasource = relationship('XmlDataSource',
                              foreign_keys=[datasource_id])


class Field(db.Model, BaseMixin):
    TYPES = Field.PROCESS_STRATEGIES.keys()
    TRANSFORM_TYPES = ['json', 'csv']

    name = db.Column(db.String(200), nullable=False)
    type_ = db.Column(db.Enum(*TYPES, name='xml_field_types'))
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

    script_id = db.Column(db.ForeignKey('script.id', ondelete='CASCADE'))
    script = relationship('Script', foreign_keys=[script_id])

    entity_id = db.Column(db.ForeignKey('entity.id', ondelete='CASCADE'))
    entity = relationship('Entity', foreign_keys=[entity_id], backref='fields')
