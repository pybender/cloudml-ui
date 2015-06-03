"""
Initializes log messages REST API.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api import api
from dynamodb.views import LogResource


api.add_resource(LogResource, '/cloudml/logs/')
