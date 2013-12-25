from api import admin
from api.base.admin import BaseAdmin
from models import Instance


class InstanceAdmin(BaseAdmin):
    Model = Instance
    column_list = ['id', 'name', 'ip', 'type', 'is_default']
    column_sortable_list = (
        ('type', Instance.type),
        ('ip', Instance.ip),
        ('is_default', Instance.is_default),
    )

admin.add_view(InstanceAdmin(
    name='Instance', category='Instances'))
