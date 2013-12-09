import logging

from utils import FeaturePredefinedItemsTestMixin, FeatureItemsTestMixin
from ..views import TransformerResource
from ..models import Feature, PredefinedTransformer
from ..fixtures import PredefinedTransformerData, FeatureData


class PredefinedTransformersTests(FeaturePredefinedItemsTestMixin):
    """
    Tests of the Predefined Transformers API.
    """
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = TransformerResource
    Model = PredefinedTransformer
    datasets = (PredefinedTransformerData, )

    OBJECT_NAME = 'transformer'
    DATA = {'type': 'Count',
            'name': 'Test Transformer',
            'params': '{"charset":"utf-8"}'}

    def setUp(self):
        super(PredefinedTransformersTests, self).setUp()
        self.obj = PredefinedTransformer.query.all()[0]

    def test_list(self):
        resp = self.check_list(show='name')
        resp = resp['transformers']
        self.assertTrue(len(resp), "No transformers returned")

    def test_details(self):
        resp = self.check_details(
            show='name,ip,is_default,type', obj=self.obj)
        tr_resp = resp['transformer']
        self.assertEqual(tr_resp['name'], self.obj.name)
        self.assertEqual(tr_resp['type'], self.obj.type)

    def test_add(self):
        self._test_add()

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.info("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

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

        transformer = PredefinedTransformer.query.all()[0]
        data = {'name': transformer.name,
                'type': 'Count'}
        _check(data, errors={
            'fields': 'name of predefined item should be unique'})

    def test_edit(self):
        self._test_edit()

    def test_delete_predefined_transformer(self):
        obj = PredefinedTransformer.query.all()[1]
        self.check_delete(obj=obj)


class FeatureTransformersTests(FeatureItemsTestMixin):
    datasets = (FeatureData, PredefinedTransformerData)
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = TransformerResource
    OBJECT_NAME = 'transformer'

    DATA = {'type': 'Count',
            'name': 'Test Transformer',
            'params': '{"charset":"utf-8"}'}

    def setUp(self):
        super(FeatureTransformersTests, self).setUp()
        self.feature = Feature.query.all()[0]

    def test_add(self):
        resp, obj = self._test_add(self.feature)
        self.assertEqual(obj, {'type': 'Count',
                               'params': {"charset":"utf-8"}})

    def test_add_from_predefined(self):
        transformer = PredefinedTransformer.query.all()[0]
        resp, obj = self._test_add_from_predefined(self.feature, transformer)
        self.assertEqual(obj['type'], transformer.type)

    def test_edit(self):
        feature = Feature.query.filter_by(
            name=FeatureData.complex_feature.name).one()
        self.assertTrue(feature.transformer, "Invalid fixtures")
        data = {'name': 'new transformer name',
                'type': 'Tfidf',
                'params': '{"lowercase": true}'}

        resp, obj = self._test_edit(feature, extra_data=data)
        self.assertEqual(obj, {'type': 'Tfidf',
                               'params': {"lowercase": True}})

    def test_edit_from_predefined(self):
        self.assertTrue(self.feature.transformer, "Invalid fixtures")
        transformer = PredefinedTransformer.query.all()[0]
        resp, obj = self._test_edit_from_predefined(self.feature, transformer)
        self.assertEqual(obj['type'], transformer.type)

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.info("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

        data = {"name": "transformer #1",
                'type': 'Count',
                'params': '{"charset":"utf-8"}',
                'feature_id': 1000}
        _check(data, errors={
            'feature_id': 'Document not found'})

        data = {'name': 'transformer #1',
                'type': 'Count',
                'predefined_selected': 'true',
                'feature_id': 1}
        _check(data, errors={'transformer': 'transformer is required'})

        transformer = PredefinedTransformer.query.all()[0]
        data = {'name': transformer.name,
                'type': 'Count'}
        _check(data, errors={
            'fields': 'name of predefined item should be unique'})
