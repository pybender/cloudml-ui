"""
Periodic tasks schedules related resources.
"""

# Authors: Anna Lysak <annalysak@cloud.upwork.com>

from api.base.resources import BaseResourceSQL
from api import api
from api.schedule.models import PeriodicTaskScenarios
from api.schedule.forms import PeriodicTaskScenariosForm


class ScheduleResource(BaseResourceSQL):
    """ Schedule API methods """
    GET_ACTIONS = ('configuration')

    # TODO: set model
    Model = PeriodicTaskScenarios
    post_form = put_form = PeriodicTaskScenariosForm

    def _get_configuration_action(self, **kwargs):
        from api.tasks import ALLOWED_PERIODIC_TASKS
        return self._render({'configuration': ALLOWED_PERIODIC_TASKS})


api.add_resource(ScheduleResource, '/cloudml/schedule/')
