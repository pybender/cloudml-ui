from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from api.import_handlers.models import ImportHandler, PredefinedDataSource


class ImportHandlerAdmin(BaseAdmin):
    Model = ImportHandler
    form_excluded_columns = ('datasets', )
    column_list = ['id', 'name', 'import_params']
    column_filters = ('name', )

admin.add_view(ImportHandlerAdmin(
    name='Import Handler', category='Import Handlers'))


class PredefinedDataSourceAdmin(BaseAdmin):
    Model = PredefinedDataSource
    column_list = ['name', 'type', 'db']

admin.add_view(PredefinedDataSourceAdmin(
    name='Data Source', category='Predefined'))
