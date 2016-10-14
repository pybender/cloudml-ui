"""
Periodic tasks schedules related resources.
"""

# Authors: Anna Lysak <annalysak@cloud.upwork.com>

from api.base.resources import BaseResourceSQL
from api import api


class ScheduleResource(BaseResourceSQL):
    """ Schedule API methods """
    GET_ACTIONS = ('task_configuration', 'schedule_configuration')

    # TODO: set model
    # Model = Schedule

    def _get_task_configuration_action(self, **kwargs):
        from api.tasks import ALLOWED_PERIODIC_TASKS
        return self._render({'configuration': ALLOWED_PERIODIC_TASKS})

    def _get_schedule_configuration_action(self, **kwargs):
        from api.tasks import ALLOWED_PERIODIC_TASKS
        return self._render({'configuration': ALLOWED_PERIODIC_TASKS})

api.add_resource(ScheduleResource, '/cloudml/schedule/')
