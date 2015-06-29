from api import admin
from api.base.admin import BaseAdmin
from api.import_handlers.models import PredefinedDataSource


class PredefinedDataSourceAdmin(BaseAdmin):
    Model = PredefinedDataSource
    column_list = ['name', 'type', 'db']

admin.add_view(PredefinedDataSourceAdmin(
    name='Data Source', category='Predefined'))
