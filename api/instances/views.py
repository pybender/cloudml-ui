from api import api
from api.base.resources import BaseResourceSQL

from models import Instance
from forms import InstanceForm


class InstanceResource(BaseResourceSQL):
    """ Instances API methods """
    Model = Instance
    put_form = post_form = InstanceForm

api.add_resource(InstanceResource, '/cloudml/aws_instances/')
