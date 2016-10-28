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
    Model = PeriodicTaskScenarios
    post_form = put_form = PeriodicTaskScenariosForm


api.add_resource(ScheduleResource, '/cloudml/schedules/')
