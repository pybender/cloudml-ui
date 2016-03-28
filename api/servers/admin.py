from wtforms import validators
from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from models import Server, ServerModelVerification, \
    VerificationExample


class ServerAdmin(BaseAdmin):
    Model = Server
    column_list = ['id', 'name', 'ip', 'folder', 'is_default', 'memory_mb',
                   'type', 'logs_url']
    column_sortable_list = (
        ('ip', Server.ip),
        ('folder', Server.folder),
        ('is_default', Server.is_default),
        ('memory_mb', Server.memory_mb),
        ('type', Server.type)
    )
    form_args = dict(memory_mb=dict(label='Memory Size (MB)'))
    column_formatters = {
        'logs_url': macro('render_link')
    }

admin.add_view(ServerAdmin(name='Server'))


class ServerModelVerificationAdmin(BaseAdmin):
    Model = ServerModelVerification
    column_formatters = {
        'server': macro('render_fk_link'),
        'model': macro('render_fk_link'),
        'import_handler': macro('render_fk_link'),
        'test_result': macro('render_fk_link'),
    }
    column_filters = ('status', )
    column_list = [
        'id', 'server', 'model', 'import_handler',
        'test_result', 'status']

admin.add_view(ServerModelVerificationAdmin(
    name='Server Model Verification', category='Verification'))


class VerificationExampleAdmin(BaseAdmin):
    Model = VerificationExample
    MIX_METADATA = False
    column_formatters = {
        'example': macro('render_fk_link'),
        'verification': macro('render_fk_link'),
    }
    column_list = ['id', 'example', 'verification']

admin.add_view(VerificationExampleAdmin(
    name='Verification Example', category='Verification'))
