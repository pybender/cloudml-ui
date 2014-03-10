from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from api.import_handlers.models import DataSet


class DataSetAdmin(BaseAdmin):
    Model = DataSet
    column_formatters = {
        # 'import_handler': macro('render_fk_link'),
        'status': macro('status_with_error')}
    column_list = ['name', 'status', 'import_params']
    column_filters = ('status', )

admin.add_view(DataSetAdmin(
    name='Data Set', category='Import Handlers'))