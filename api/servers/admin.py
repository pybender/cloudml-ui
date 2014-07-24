from api import admin
from api.base.admin import BaseAdmin
from models import Server


class ServerAdmin(BaseAdmin):
    Model = Server
    column_list = ['id', 'name', 'ip', 'folder', 'is_default']
    column_sortable_list = (
        ('ip', Server.ip),
        ('folder', Server.folder),
        ('is_default', Server.is_default),
    )

admin.add_view(ServerAdmin(
    name='Server', category='Models'))
