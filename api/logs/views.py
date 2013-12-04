from api import api
from mongo.views import LogResource


api.add_resource(LogResource, '/cloudml/logs/')
