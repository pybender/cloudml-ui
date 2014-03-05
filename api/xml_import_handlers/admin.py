from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from models import *


class ImportHandlerAdmin(BaseAdmin):
    Model = XmlImportHandler
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(ImportHandlerAdmin(
    name='XML Import Handler', category='XML Import Handlers'))


class XmlDataSourceAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlDataSource
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(XmlDataSourceAdmin(
    name='XML Data Source', category='XML Import Handlers'))


class InputParameterAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = InputParameter
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(InputParameterAdmin(
    name='Input Parameter', category='XML Import Handlers'))


class ScriptAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = Script
    column_list = ['id']

admin.add_view(ScriptAdmin(
    name='Script', category='XML Import Handlers'))


class QueryAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = Query
    column_list = ['id']

admin.add_view(QueryAdmin(
    name='Query', category='XML Import Handlers'))


class EntityAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = Entity
    column_list = ['id', 'name']

admin.add_view(EntityAdmin(
    name='Entity', category='XML Import Handlers'))


class FieldAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = Field
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(FieldAdmin(
    name='Entity Field', category='XML Import Handlers'))
