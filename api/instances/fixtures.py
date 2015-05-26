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
