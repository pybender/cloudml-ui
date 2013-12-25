from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from models import ImportHandler, PredefinedDataSource, DataSet


class ImportHandlerAdmin(BaseAdmin):
    Model = ImportHandler
    column_list = ['name', 'import_params']
    column_filters = ('name', )

admin.add_view(ImportHandlerAdmin(
    name='Import Handler', category='Import Handlers'))


class PredefinedDataSourceAdmin(BaseAdmin):
    Model = PredefinedDataSource
    column_list = ['name', 'type', 'db']

admin.add_view(PredefinedDataSourceAdmin(
    name='Data Source', category='Predefined'))


class DataSetAdmin(BaseAdmin):
    Model = DataSet
    column_formatters = {
        'import_handler': macro('render_fk_link'),
        'status': macro('status_with_error')}
    column_list = ['name', 'status', 'import_params', 'import_handler']
    column_filters = ('status', 'import_handler')

admin.add_view(DataSetAdmin(
    name='Data Set', category='Import Handlers'))
