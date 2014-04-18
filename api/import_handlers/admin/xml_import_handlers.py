from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from api.import_handlers.models import XmlScript, XmlQuery, XmlEntity, \
    XmlField, XmlImportHandler, XmlDataSource, XmlInputParameter, XmlSqoop


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
    column_formatters = {'import_handler': macro('render_fk_link'), }
    column_list = ['id', 'name', 'type', 'regex', 'format', 'import_handler']
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
    column_list = ['id', 'name', 'datasource',
                   'datasource_name']
    column_formatters = {
        'datasource': macro('render_fk_link')}


admin.add_view(EntityAdmin(
    name='XML Entity', category='Import Handlers'))


class FieldAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlField
    column_list = ['id', 'name', 'type', 'column', 'jsonpath', 'join',
                   'regex', 'split', 'dateFormat', 'transform', 'required',
                   'multipart']
    column_filters = ('name', )

admin.add_view(FieldAdmin(
    name='XML Entity Field', category='Import Handlers'))


class SqoopAdmin(BaseAdmin):
    MIX_METADATA = False
    Model = XmlSqoop
    column_list = ['id', 'entity', 'target', 'table', 'datasource']
    column_formatters = {
        'entity': macro('render_fk_link'),
        'datasource': macro('render_fk_link')
    }

admin.add_view(SqoopAdmin(
    name='XML Sqoop Import', category='Import Handlers'))
