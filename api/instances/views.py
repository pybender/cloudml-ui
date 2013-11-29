from api import api
from api.resources import BaseResourceSQL
from models import Instance
from forms import InstanceForm


class InstanceResource(BaseResourceSQL):
    """
    Instances API methods
    """
    MESSAGE404 = "Instance doesn't exist"
    OBJECT_NAME = 'instance'
    Model = Instance
    OBJECT_NAME = 'instance'

    put_form = post_form = InstanceForm

api.add_resource(InstanceResource, '/cloudml/aws_instances/')
