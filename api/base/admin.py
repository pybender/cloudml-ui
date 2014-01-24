from flask.ext.admin.contrib import sqla
from flask.ext.admin.model.template import macro

from api import app


class BaseAdmin(sqla.ModelView):
    Model = None
    column_display_pk = True
    MIX_METADATA = True
    list_template = 'admin/model/object_list.html'
    column_default_sort = 'id'
    form_widget_args = {
        'created_by': {'disabled':True},
        'created_on': {'disabled':True},
        'updated_by': {'disabled':True},
        'updated_on': {'disabled':True}
    }

    def is_accessible(self):  # TODO: ?
        return True

    def __init__(self, *args, **kwargs):
        if self.MIX_METADATA:
            if self.column_list:
                self.column_list.append('created')
                self.column_list.append('updated')
            self.column_formatters['created'] = macro('render_created')
            self.column_formatters['updated'] = macro('render_updated')
            self.column_filters = list(self.column_filters or [])
            self.column_filters.append('created_on')
        super(BaseAdmin, self).__init__(
            self.Model, app.sql_db.session, *args, **kwargs)
