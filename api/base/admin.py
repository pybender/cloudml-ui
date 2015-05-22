from flask.ext.admin.contrib import sqla
from flask.ext.admin.model.template import macro
from flask import request

from sqlalchemy.orm import exc as orm_exc

from api import app
from api.accounts.models import User


class BaseAdmin(sqla.ModelView):
    Model = None
    column_display_pk = True
    MIX_METADATA = True
    list_template = 'admin/model/object_list.html'
    column_default_sort = 'id'
    form_excluded_columns = ['created_by', 'created_on', 'updated_by',
                             'updated_on']

    def is_accessible(self):  # TODO: ?
        # TODO: nader20141214, I don't know how the frontend sets the cookies
        # but nevertheless that cookie is the same as the user hash we use
        # to access the backend apis
        auth_token = request.cookies.get('auth-token', None)
        if auth_token is None:
            return False
        # The frontend puts a space on front off the auth-token we need to
        # disable this
        auth_token = auth_token.replace('%22', '')
        try:
            request.user = User.query.filter_by(
                auth_token=User.get_hash(auth_token)).one()
        except orm_exc.NoResultFound:
            request.user = None

        return request.user is not None

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

    def after_model_change(self, form, model, is_created):
        # TODO: nader20141214, we still dont have a way to set the request user
        # as we don't have any form of authentication.
        model.save()
