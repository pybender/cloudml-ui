import logging

from utils import FeaturePredefinedItems
from ..views import TransformerResource
from ..models import Feature, PredefinedTransformer


class PredefinedTransformersTests(FeaturePredefinedItems):
    """
    Tests of the Predefined Transformers API.
    """
    TRANSFORMER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('feature_sets.json', 'transformers.json',
                'features.json', 'complex_features.json')
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = TransformerResource
    Model = PredefinedTransformer

    OBJECT_NAME = 'transformer'
    DATA = {'type': 'Count',
            'name': 'Test Transformer',
            'params': '{"charset":"utf-8"}'}

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        instance = self.Model.query.filter_by(name='Instance 1')[0]
        resp = self.check_details(
            show='name,ip,is_default,type', obj=instance)
        instance_resp = resp['instance']
        self.assertEqual(instance_resp['name'], instance.name)
        self.assertEqual(instance_resp['type'], instance.type)
        self.assertEqual(instance_resp['ip'], instance.ip)
        self.assertEqual(instance_resp['is_default'], 'False')

    def test_add_predefined_transformer(self):
        self._test_add_predefined()

    def test_add_feature_transformer(self):
        feature = self.db.Feature.find_one()
        self._test_add_feature_item(feature)

    def add_feature_transformer_from_predefined(self):
        feature = self.db.Feature.find_one()
        transformer = self.db.Transformer.find_one()
        self._add_feature_item_from_predefined(feature, transformer)

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.debug("Checking validation with data %s", data)
            resp = self._check_post(data, error='err')
            self._check_errors(resp, errors)

        data = {"name": "transformer #1",
                'type': 'invalid'}
        _check(data, errors={
            'type': 'should be one of Count, Tfidf, Lda, Dictionary, Lsi'})

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
            'feature_id': 'Document not found'})

        data = {'name': 'transformer #1',
                'type': 'Count',
                'predefined_selected': 'true',
                'feature_id': '525123b1106a6c5bcbc12efb'}
        _check(data, errors={'transformer': 'transformer is required'})

        transformer = self.db.Transformer.find_one()
        data = {'name': transformer.name,
                'type': 'Count'}
        _check(data, errors={
            'fields': 'name of predefined item should be unique'})

    def test_edit_predefined_transformer(self):
        self._test_edit_predefined_item()

    def test_edit_feature_transformer(self):
        feature = self.db.Feature.get_from_id(
            ObjectId('525123b1206a6c5bcbc12efb'))
        self.assertTrue(feature.transformer, "Invalid fixtures")
        data = {'name': 'new transformer name',
                'type': 'Tfidf',
                'params': '{"lowercase": true}'}

        self._test_edit_feature_item(feature, extra_data=data)

    def test_edit_feature_transformer_from_predefined(self):
        feature = Feature.query.filter_by(name="Feature").one()
        #    ObjectId('525123b1206a6c5bcbc12efb')
        self.assertTrue(feature.transformer, "Invalid fixtures")

        transformer = self.db.Transformer.find_one()
        self._edit_feature_item_from_predefined(feature, transformer)

    def test_delete_predefined_transformer(self):
        self._check_delete()
