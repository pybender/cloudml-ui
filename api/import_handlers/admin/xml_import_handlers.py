from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from api.import_handlers.models import XmlScript, XmlQuery, XmlEntity, XmlField, \
    XmlImportHandler, XmlDataSource, XmlInputParameter


class ImportHandlerAdmin(BaseAdmin):
    Model = XmlImportHandler
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(ImportHandlerAdmin(
    name='XML Import Handler', category='Import Handlers'))


class XmlDataSourceAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlDataSource
    column_list = ['id', 'name', 'type', 'params']
    column_filters = ('name', )

admin.add_view(XmlDataSourceAdmin(
    name='XML Data Source', category='Import Handlers'))


class InputParameterAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlInputParameter
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(InputParameterAdmin(
    name='XML Input Parameter', category='Import Handlers'))


class ScriptAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlScript
    column_list = ['id']

admin.add_view(ScriptAdmin(
    name='XML Script', category='Import Handlers'))


class QueryAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlQuery
    column_list = ['id']

admin.add_view(QueryAdmin(
    name='XML Query', category='Import Handlers'))


class EntityAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlEntity
    column_list = ['id', 'name']

admin.add_view(EntityAdmin(
    name='XML Entity', category='Import Handlers'))


class FieldAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlField
    column_list = ['id', 'name']
    column_filters = ('name', )

admin.add_view(FieldAdmin(
    name='XML Entity Field', category='Import Handlers'))
