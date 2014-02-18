from api import api
from api.base.resources import BaseResourceSQL

from models import Server


class ServerResource(BaseResourceSQL):
    """ Servers API methods """
    Model = Server
    ALLOWED_METHODS = ('get', 'options')

api.add_resource(ServerResource, '/cloudml/servers/')
