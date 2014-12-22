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
    form_excluded_columns = \
        BaseAdmin.form_excluded_columns + \
        ['cluster', 'status', 'error', 'data', 'import_handler_id',
         'import_handler_type', 'pig_step', 'on_s3', 'compress', 'filename',
         'filesize', 'records_count', 'time', 'data_fields', 'format', 'uid',
         'parent_json', 'parent_xml']

admin.add_view(DataSetAdmin(
    name='Data Set', category='Import Handlers'))
