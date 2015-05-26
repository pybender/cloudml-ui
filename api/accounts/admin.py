# Authors: Nikolay Melnik <nmelnik@upwork.com>

from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from api.accounts.models import User


class UserAdmin(BaseAdmin):
    Model = User
    MIX_METADATA = False
    column_searchable_list = ('name', 'uid')
    column_formatters = {'odesk_url': macro('render_link')}
    column_exclude_list = ('auth_token', 'portrait_32_img')

admin.add_view(UserAdmin())
