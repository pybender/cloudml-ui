"""
Database fixtures for instance related models.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from fixture import DataSet


class InstanceData(DataSet):
    class instance_01:
        name = "Instance 1"
        description = "Some description"
        type = "small"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        ip = "0.0.0.0"
        is_default = False

    class instance_02:
        name = "Instance 2"
        description = "Some description"
        type = "small"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        ip = "1.0.0.0"
        is_default = False

    class instance_03:
        name = "Instance 3"
        description = "Some description"
        type = "small"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        ip = "3.0.0.0"
        is_default = True


ACTIVE_CLUSTERS_COUNT = 2


class ClusterData(DataSet):
    class cluster_01:
        jobflow_id = "asdf123"
        master_node_dns = "ec2-11-11-11-111"
        created_on = "2015-04-26"
        updated_on = "2015-04-26"
        is_default = False
        status = 'New'

    class cluster_02:
        jobflow_id = "asdf124"
        master_node_dns = "ec2-12-11-11-111"
        created_on = "2015-04-26"
        updated_on = "2015-04-26"
        is_default = False
        status = 'Terminated'

    class cluster_03:
        jobflow_id = "asdf125"
        master_node_dns = "ec2-13-11-11-111"
        created_on = "2015-04-26"
        updated_on = "2015-04-26"
        is_default = True
        status = 'Error'
