from api import api
from dynamodb.views import LogResource


api.add_resource(LogResource, '/cloudml/logs/')
