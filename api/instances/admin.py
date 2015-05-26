"""
Admin part for Instances and Clusters.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api import admin
from api.base.admin import BaseAdmin
from models import Instance, Cluster


class InstanceAdmin(BaseAdmin):
    Model = Instance
    column_list = ['id', 'name', 'ip', 'type', 'is_default']
    column_sortable_list = (
        ('type', Instance.type),
        ('ip', Instance.ip),
        ('is_default', Instance.is_default),
    )


class ClusterAdmin(BaseAdmin):
    Model = Cluster
    column_list = ['id', 'jobflow_id', 'port', 'status',
                   'master_node_dns', 'is_default']


admin.add_view(InstanceAdmin(
    name='Instances', category='Instances'))

admin.add_view(ClusterAdmin(
    name='Clusters', category='Instances'))
