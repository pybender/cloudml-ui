from api import api
from api.resources import BaseResourceSQL
from models import Instance
from forms import *


class InstanceResource(BaseResourceSQL):
    """
    Instances API methods
    """
    MESSAGE404 = "Instance doesn't exist"
    OBJECT_NAME = 'instance'
    PUT_ACTIONS = ('make_default', )
    Model = Instance
    OBJECT_NAME = 'instance'

    post_form = InstanceAddForm
    put_form = InstanceEditForm

api.add_resource(InstanceResource, '/cloudml/aws_instances/')
