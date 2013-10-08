import httplib
import json
from bson import ObjectId

from utils import BaseTestCase, HTTP_HEADERS
from utils import MODEL_ID
from api.views import NamedFeatureTypeResource
from api import app


class NamedFeatureTypeTests(BaseTestCase):
    """
    Tests of the Instances API.
    """
    NAMED_TYPE_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('named_feature_types.json', )
    BASE_URL = '/cloudml/features/named_types/'
    RESOURCE = NamedFeatureTypeResource

    def setUp(self):
        super(NamedFeatureTypeTests, self).setUp()
        self.Model = self.db.NamedFeatureType
        self.obj = self.Model.get_from_id(ObjectId(self.NAMED_TYPE_ID))
        self.assertTrue(self.obj)

    def test_list(self):
        self._check_list(show='name')

    def test_details(self):
        self._check_details()

    def test_post(self):
        post_data = {'type': 'int',
                     'name': 'new'}
        resp, obj = self._check_post(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.type, post_data['type'])
