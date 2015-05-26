"""
Unittests for Model class
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import httplib
import json
from moto import mock_s3
import tempfile
from mock import patch
import numpy
import os

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, \
    HTTP_HEADERS, FEATURE_COUNT, TARGET_VARIABLE
from api.features.models import FeatureSet, Feature
from api.ml_models.tasks import transform_dataset_for_download
from api.ml_models.views import ModelResource
from api.ml_models.models import Model, Tag, db, Segment, Weight
from api.import_handlers.models import DataSet, ImportHandler, XmlImportHandler
from api.instances.models import Instance
from api.instances.fixtures import InstanceData
from api.model_tests.models import TestResult, TestExample
from api.model_tests.fixtures import TestResultData, TestExampleData
from api.features.fixtures import FeatureSetData, FeatureData
from api.servers.models import Server
from api.async_tasks.models import AsyncTask
from api.servers.fixtures import ServerData
from api.ml_models.fixtures import ModelData, TagData
from api.import_handlers.fixtures import ImportHandlerData, DataSetData, \
    XmlImportHandlerData, XmlEntityData, XmlFieldData


class ModelTests(BaseDbTestCase):
    """
    Tests for api.ml_models.models.Model class.
    """
    datasets = [ImportHandlerData, DataSetData, ModelData,
                XmlImportHandlerData]

    def test_generic_relation_to_import_handler(self):
        model = Model(name="test1")
        handler = ImportHandler.query.first()
        xml_handler = XmlImportHandler.query.first()
        model.test_import_handler = handler
        model.train_import_handler = xml_handler
        model.save()

        self.assertEqual(model.test_import_handler, handler)
        self.assertEqual(model.test_import_handler_id, handler.id)
        self.assertEqual(model.test_import_handler_type, 'json')
        self.assertEqual(model.train_import_handler, xml_handler)
        self.assertEqual(model.train_import_handler_id, xml_handler.id)
        self.assertEqual(model.train_import_handler_type, 'xml')

        model.test_import_handler = xml_handler
        model.train_import_handler = handler
        model.save()

        self.assertEqual(model.train_import_handler, handler)
        self.assertEqual(model.train_import_handler_type, 'json')
        self.assertEqual(model.test_import_handler, xml_handler)
        self.assertEqual(model.test_import_handler_type, 'xml')

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    def test_get_trainer_s3url(self, *mocks):
        model = Model(name="test", trainer='trainer file',
                      status=Model.STATUS_TRAINED)
        model.save()
        url = model.get_trainer_s3url()
        trainer_filename = model.get_trainer_filename()
        self.assertTrue(trainer_filename)
        self.assertTrue(url)
        self.assertTrue(
            's3.amazonaws.com/%s?Signature' % trainer_filename in url)
        self.assertTrue(url.startswith('https://'))

        # trainer file not yet uploaoded
        model = Model.query.filter_by(name='OtherModel').first()
        self.assertTrue(model)
        url = model.get_trainer_s3url()
        self.assertEqual(None, url)

        # not trained
        model = Model.query.filter_by(name='NewModel').first()
        self.assertTrue(model)
        url = model.get_trainer_s3url()
        self.assertEqual(None, url)

    def test_visualize_model(self):
        model = Model.query.first()

        def check(params, result, initial_visualization_data=None):
            model.visualization_data = initial_visualization_data or {}
            model.save()
            model.visualize_model(**params)
            obj = Model.query.get(model.id)
            self.assertEqual(obj.visualization_data, result)

        check({}, {})
        check(
            {'data': {'smth': 'val'}},
            {'smth': 'val'})
        check(
            {'data': {'smth': 'val'}, 'status': 'done'},
            {'smth': 'val', u'parameters': {u'status': u'done'}})
        self.assertRaises(ValueError, check, {'segment': 'seg'}, {})
        check(
            {'data': {'smth': 'val'}, 'status': 'done', 'segment': 'seg'},
            {'seg': {'smth': 'val', u'parameters': {u'status': u'done'}}})
        check(
            {'status': 'pending'},
            {u'parameters': {u'status': u'pending'}})
        check(
            {'status': 'pending'},
            {'key': 'val', u'parameters': {u'status': u'pending'}},
            initial_visualization_data={'key': 'val'})
