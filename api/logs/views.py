from api import api
from simpledb.views import LogResource


api.add_resource(LogResource, '/cloudml/logs/')
