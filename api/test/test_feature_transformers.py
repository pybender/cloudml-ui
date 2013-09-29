import json
from bson import ObjectId

from utils import BaseTestCase
from api.views import TransformerResource


class TransformersTests(BaseTestCase):
    """
    Tests of the Transformers API.
    """
    TRANSFORMER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('transformers.json', )
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = TransformerResource

    def setUp(self):
        super(TransformersTests, self).setUp()
        self.Model = self.db.Transformer
        self.obj = self.Model.get_from_id(ObjectId(self.TRANSFORMER_ID))
        self.assertTrue(self.obj)

    def test_list(self):
        self._check_list(show='name')

    def test_filter(self):
        self._check_filter({'is_predefined': 1}, {'is_predefined': True})

    def test_details(self):
        self._check_details()

    def test_post(self):
        # Adding predefined Transformer
        post_data = {'type': 'Count',
                     'name': 'Test Transformer',
                     'params': '{"charset":"utf-8"}'}
        resp, obj = self._check_post(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.type, post_data['type'])
        self.assertTrue(obj.is_predefined)
        self.assertEqual(obj.params, {"charset": "utf-8"})

        # Edditing predefined transformer
        data = {'name': 'Test Transformer #2',
                'type': 'Tfidf', }
        resp, obj = self._check_put(data, load_model=True)
        rdata = json.loads(resp.data)
        self.assertEquals(rdata['transformer']['name'], str(obj.name))
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])

        # TODO: Adding transformer to the feature

        # TODO: Edditing feature transformer

    def test_delete(self):
        self._check_delete()

        # TODO: check deleting feature transformer
