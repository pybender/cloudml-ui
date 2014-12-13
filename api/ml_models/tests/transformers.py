import logging
import json
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from ..views import TransformerResource
from ..models import Transformer
from api.features.models import Feature
from ..fixtures import TransformerData
from api.features.fixtures import FeatureData
from api.import_handlers.fixtures import XmlImportHandlerData, DataSetData, \
    ImportHandlerData
from api.instances.fixtures import InstanceData
from api.instances.models import Instance
from api.import_handlers.models import XmlImportHandler, DataSet, ImportHandler


class PretrainedTransformersTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Pretrained Transformers API.
    """
    BASE_URL = '/cloudml/transformers/'
    RESOURCE = TransformerResource
    Model = Transformer
    datasets = (TransformerData, ImportHandlerData,
                DataSetData, XmlImportHandlerData, InstanceData)

    DATA = {'type': 'Count',
            'name': 'Test Transformer',
            'params': '{"charset":"utf-8"}'}

    def setUp(self):
        super(PretrainedTransformersTests, self).setUp()
        self.obj = Transformer.query.filter_by(
            name=TransformerData.transformer_01.name).first()
        self.xml_handler = XmlImportHandler.query.first()
        self.instance = Instance.query.filter_by(
            name=InstanceData.instance_01.name).first()
        self.handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        # TODO: Why we need it? Could we create link to import handler
        # using fixtures. Investigate why refs to another fixtures doesn't
        # works
        self.obj.train_import_handler = self.handler
        self.obj.save()

    def test_list(self):
        resp = self.check_list(show='name,field_name,feature_type')
        transformers = resp['transformers']
        self.assertTrue(len(transformers), "No transformers returned")

    def test_details(self):
        resp = self.check_details(
            show='name,field_name,feature_type,type,params', obj=self.obj)
        tr_resp = resp['transformer']
        self.assertEqual(tr_resp['name'], self.obj.name)
        self.assertEqual(tr_resp['type'], self.obj.type)
        self.assertEqual(tr_resp['feature_type'], self.obj.feature_type)
        self.assertEqual(tr_resp['field_name'], self.obj.field_name)
        self.assertEqual(tr_resp['params'], self.obj.params)

    def test_post_form(self):
        post_data = {
            'train_import_handler': '%sxml' % self.xml_handler.id,
            'name': 'transformer',
            'field_name': 'title',
            'feature_type': 'text',
            'type': 'Count'}
        resp, transformer = self.check_edit(post_data)
        self.assertEquals(transformer.name, post_data['name'])
        self.assertEquals(transformer.field_name, post_data['field_name'])
        self.assertEquals(transformer.feature_type, post_data['feature_type'])
        self.assertEquals(transformer.type, post_data['type'])
        self.assertEquals(transformer.status, transformer.STATUS_NEW)
        self.assertEquals(transformer.train_import_handler, self.xml_handler)

    def test_post_json(self):
        with open('./conf/transformer.json', 'r') as fp:
            json_text = fp.read()

        post_data = {
            'train_import_handler': '%sxml' % self.xml_handler.id,
            'json': json_text,
            'json_selected': 'true'}
        resp, transformer = self.check_edit(post_data)

        json_data = json.loads(json_text)
        self.assertEquals(transformer.name, json_data['transformer-name'])
        self.assertEquals(transformer.field_name, json_data['field-name'])
        self.assertEquals(transformer.feature_type, json_data['type'])
        self.assertEquals(transformer.type, json_data['transformer']['type'])
        self.assertEquals(transformer.status, transformer.STATUS_NEW)
        self.assertEquals(transformer.train_import_handler, self.xml_handler)

    def test_put(self):
        put_data = {'name': 'new-name'}
        data, transformer = self.check_edit(put_data, id=self.obj.id)
        self.assertEquals(data['transformer']['name'], transformer.name)
        self.assertEquals(data['transformer']['name'], put_data['name'])

        put_data = {'field_name': 'new-field-name'}
        data, transformer = self.check_edit(put_data, id=self.obj.id)
        self.assertEquals(transformer.field_name, put_data['field_name'])

    @mock_s3
    def test_train(self, *mocks):
        ds = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': False,
                'dataset': ds.id}
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, obj.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds.name])

        self.assertEqual(obj.trained_by.uid, 'user')
        self.assertTrue(obj.memory_usage > 0)

    def test_delete(self):
        self.check_delete(obj=self.obj)


class FeatureTransformersTests(BaseDbTestCase, TestChecksMixin):
    datasets = (FeatureData, TransformerData)
    BASE_URL = '/cloudml/transformers/'
    RESOURCE = TransformerResource
    OBJECT_NAME = 'transformer'

    DATA = {'type': 'Count',
            'name': 'Test Transformer',
            'params': '{"charset":"utf-8"}'}

    def setUp(self):
        super(FeatureTransformersTests, self).setUp()
        self.feature = Feature.query.all()[0]
        self.transformer = Transformer.query.filter_by(
            name=TransformerData.transformer_01.name).first()

    def test_simple(self):
        post_data = {
            'feature_id': self.feature.id,
            'name': 'transformer',
            'type': 'Count',
            'params': '{"separator": ","}'}
        resp = self._check(data=post_data, method='post')
        feature = Feature.query.get(self.feature.id)
        self.assertDictEqual(feature.transformer, {
            'type': 'Count',
            'params': {"separator": ","},
            'id': -1
        })

    def test_pretrained(self):
        post_data = {
            'feature_id': self.feature.id,
            'transformer': self.transformer.id,
            'predefined_selected': 'true'}
        resp = self._check(data=post_data, method='post')
        feature = Feature.query.get(self.feature.id)
        self.assertDictEqual(feature.transformer, {
            'type': self.transformer.name,
            'id': self.transformer.id
        })
