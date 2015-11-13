from wtforms import validators

from api import admin
from api.base.admin import BaseAdmin
from models import Server


class ServerAdmin(BaseAdmin):
    Model = Server
    column_list = ['id', 'name', 'ip', 'folder', 'is_default', 'memory_mb',
                   'type']
    column_sortable_list = (
        ('ip', Server.ip),
        ('folder', Server.folder),
        ('is_default', Server.is_default),
        ('memory_mb', Server.memory_mb),
        ('type', Server.type)
    )
    form_args = dict(memory_mb=dict(label='Memory Size (MB)'))

admin.add_view(ServerAdmin(name='Server'))
