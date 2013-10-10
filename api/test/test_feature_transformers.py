import json
import logging
from bson import ObjectId

from utils import BaseTestCase
from api.views import TransformerResource


class TransformersTests(BaseTestCase):
    """
    Tests of the Transformers API.
    """
    TRANSFORMER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('transformers.json', 'features.json')
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

    def test_add_predefined_transformer(self):
        post_data = {'type': 'Count',
                     'name': 'Test Transformer',
                     'params': '{"charset":"utf-8"}',
                     'is_predefined': 'True'}
        resp, obj = self._check_post(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.type, post_data['type'])
        self.assertTrue(obj.is_predefined)
        self.assertEqual(obj.params, {"charset": "utf-8"})

    def test_add_feature_transformer(self):
        feature = self.db.Feature.find_one()
        data = {'type': 'Count',
                'name': 'Test Transformer',
                'params': '{"charset":"utf-8"}',
                'is_predefined': 'false',
                'feature_id': str(feature._id)}
        resp, obj = self._check_post(data, load_model=True)
        self.assertEqual(obj.name, data['name'])
        self.assertEqual(obj.type, data['type'])
        self.assertFalse(obj.is_predefined)
        self.assertEqual(obj.params, {"charset": "utf-8"})

        feature = self.db.Feature.find_one({'_id': feature._id})
        self.assertTrue(feature.transformer,
                        "Transformer of the feature should be filled")

    def add_feature_transformer_from_predefined(self):
        feature = self.db.Feature.find_one()
        transformer = self.db.Transformer.find_one({'is_predefined': True})
        data = {'transformer': transformer.name,
                'feature_id': str(feature._id),
                'predefined_selected': 'true'}
        resp, obj = self._check_post(data, load_model=True)
        self.assertEqual(obj.name, transformer.name)
        self.assertEqual(obj.type, transformer.type)
        self.assertFalse(obj.is_predefined)
        self.assertEqual(obj.params, transformer.params)

        feature = self.db.Feature.find_one({'_id': feature._id})
        self.assertTrue(feature.transformer,
                        "Transformer of the feature should be filled")

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.debug("Checking validation with data %s", data)
            resp = self._check_post(data, error='err')
            self._check_errors(resp, errors)

        data = {"name": "transformer #1"}
        _check(data, errors={
            'type': 'type is required',
            'fields': 'one of feature_id and is_predefined is required'})

        data['type'] = 'invalid'
        data["is_predefined"] = True
        _check(data, errors={
            'type': 'should be one of Count, Tfidf, Dictionary'})

        data['type'] = 'Count'
        data["params"] = 'hello!'
        _check(data, errors={'params': 'invalid json: hello!'})

        # TODO: check that valid parameters filled
        # _check({"type": "Tfidf", "params": '{"a": 1}'}, errors={
        #     'params': 'parameter a not found'})

        # TODO: we should not have 500 error here
        data['params'] = '{"charset":"utf-8"}'
        # data['feature_id'] = 'id'
        # _check(data, errors={})

        # is_predefined and invalid feature_id is specified
        data["feature_id"] = '5170dd3a106a6c1631000000'
        _check(data, errors={
            'feature_id': 'Document not found',
            'fields': 'one of feature_id and is_predefined is required'})

        # is_predefined and valid feature_id is specified
        data['feature_id'] = '525123b1106a6c5bcbc12efb'
        _check(data, errors={
            'fields': 'one of feature_id and is_predefined is required'})

        data = {'name': 'transformer #1',
                'type': 'Count',
                'predefined_selected': 'true',
                'is_predefined': False,
                'feature_id': '525123b1106a6c5bcbc12efb'}
        _check(data, errors={'transformer': 'transformer is required'})

        data = {'is_predefined': True,
                'name': 'Words count',
                'type': 'Count'}
        _check(data, errors={
            'fields': 'name of predefined item should be unique'})

    def test_edit_predefined_transformer(self):
        data = {'name': 'predefined Transformer',
                'type': 'Tfidf',
                'is_predefined': True}
        resp, obj = self._check_put(data, load_model=True)
        rdata = json.loads(resp.data)
        self.assertEquals(rdata['transformer']['name'], str(obj.name))
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])

    def test_edit_feature_transformer(self):
        # TODO:
        pass

    def test_edit_feature_transformer_from_predefined(self):
        # TODO:
        pass

    def test_delete_predefined_transformer(self):
        self._check_delete()

    def test_delete_feature_transformer(self):
        # TODO: check deleting feature transformer
        pass
