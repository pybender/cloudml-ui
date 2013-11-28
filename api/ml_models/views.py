from api import api
from api.resources import BaseResourceSQL
from models import Tag


class TagResource(BaseResourceSQL):
    """
    Tags API methods
    """
    MESSAGE404 = "Tag doesn't exist"
    OBJECT_NAME = 'tag'
    DEFAULT_FIELDS = [u'_id']
    Model = Tag

api.add_resource(TagResource, '/cloudml/tags/')
