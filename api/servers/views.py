from api import api
from api.base.resources import BaseResourceSQL

from models import Server
from forms import ServerForm


class ServerResource(BaseResourceSQL):
    """ Servers API methods """
    Model = Server
    put_form = post_form = ServerForm

api.add_resource(ServerResource, '/cloudml/servers/')
