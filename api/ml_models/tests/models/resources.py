"""
Unittests for ModelResource
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import httplib
import json
from moto import mock_s3
from mock import patch

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, \
    HTTP_HEADERS, FEATURE_COUNT, TARGET_VARIABLE
from api.features.models import FeatureSet, Feature
from api.ml_models.views import ModelResource
from api.ml_models.models import Model, Tag, db, Segment, Weight
from api.servers.models import Server
from api.servers.fixtures import ServerData
from api.import_handlers.models import DataSet, \
    XmlImportHandler as ImportHandler
from api.instances.fixtures import InstanceData
from api.model_tests.fixtures import TestResultData, TestExampleData
from api.features.fixtures import FeatureSetData, FeatureData, FEATURES_STR
from api.ml_models.fixtures import ModelData, TagData, MODEL_TRAINER, \
    DECISION_TREE_WITH_SEGMENTS, TREE_VISUALIZATION_DATA, INVALID_MODEL
from api.import_handlers.fixtures import DataSetData, \
    XmlImportHandlerData as ImportHandlerData, IMPORT_HANDLER_FIXTURES
from api.import_handlers.fixtures import EXTRACT_XML, get_importhandler

TRAIN_PARAMS = json.dumps(
    {'start': '2012-12-03',
     'end': '2012-12-04',
     'category': '1'})

TRAIN_PARAMS1 = json.dumps(
    {'start': '2012-12-03',
     'end': '2012-12-04'})


class ModelResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Model API & Tasks
    """
    BASE_URL = '/cloudml/models/'
    RESOURCE = ModelResource
    Model = Model
    datasets = [FeatureData, FeatureSetData, DataSetData, ModelData,
                InstanceData, TestResultData, TestExampleData,
                TagData, ServerData] + IMPORT_HANDLER_FIXTURES

    def setUp(self):
        from api.instances.models import Instance
        super(ModelResourceTests, self).setUp()
        self.obj = Model.query.filter_by(
            name=ModelData.model_01.name).first()

        self.handler = get_importhandler()
        self.instance = Instance.query.filter_by(
            name=InstanceData.instance_01.name).first()

        # TODO: Why we need it? Could we create link to import handler
        # using fixtures. Investigate why refs to another fixtures doesn't
        # works
        self.obj.test_import_handler = self.obj.train_import_handler = \
            self.handler
        self.obj.save()

        # update features with feature_set id, as ref('id') is not working
        # also force features_set to update its representation after features
        # fixtures have been added
        feature_set = FeatureSet.query.all()[0]
        for fixture in [FeatureData.smth, FeatureData.hire_outcome_feature,
                        FeatureData.title_feature, FeatureData.name_feature,
                        FeatureData.complex_feature,
                        FeatureData.disabled_feature]:
            feature = Feature.query.filter_by(name=fixture.name).one()
            feature.feature_set_id = feature_set.id
            feature.save()

        feature_set.features_dict = feature_set.to_dict()
        feature_set.save()

    """
    GET
    """

    def test_list(self):
        self.check_list(show='')
        self.check_list(show='created_on,updated_on,name')

    def test_filter(self):
        self.check_list(data={'status': 'New'}, query_params={'status': 'New'})
        self.check_list(data={'name': 'Trained'},
                        query_params={'name': 'TrainedModel'})

    def test_details(self):
        self.check_details(show='')
        self.check_details(show='created_on,labels')
        self.check_details(show='name,test_handler_fields')

    def test_datasets(self):
        self.obj.datasets = [
            DataSet.query.filter_by(name=DataSetData.dataset_01.name).first(),
            DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()
        ]
        self.obj.save()
        resp = self.check_details(show='name,datasets')
        self.assertEquals(len(resp[self.RESOURCE.OBJECT_NAME]['datasets']), 2)

    def test_data_fields(self):
        self.obj.datasets = [
            DataSet.query.filter_by(name=DataSetData.dataset_01.name).first(),
            DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()
        ]
        self.obj.save()
        resp = self.check_details(show='name,data_fields')
        self.assertEquals(
            resp['model']['data_fields'], ['employer.country', 'opening_id'])

    def test_get_features_download_action(self):
        url = self._get_url(id=self.obj.id, action='features_download')
        resp = self.client.get(url, headers=HTTP_HEADERS)

        feature_set = json.loads(resp.data)
        self.assertEqual(5, len(feature_set['features']))
        self.assertTrue(all([f.get('disabled', False) is False
                             for f in feature_set['features']]))
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(resp.mimetype, 'application/json')
        self.assertEquals(
            resp.headers['Content-Disposition'],
            'attachment; filename=%s-features.json' % (self.obj.name, ))

        # disable a feature and regenerate
        feature = Feature.query.filter_by(name='title').one()
        feature.disabled = True
        feature.save()
        url = self._get_url(id=self.obj.id, action='features_download')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        feature_set = json.loads(resp.data)
        self.assertEqual(4, len(feature_set['features']))

    def test_get_trainer_download_s3url_action(self):
        model = Model.query.filter_by(name='TrainedModel').first()
        self.assertTrue(model)
        url = self._get_url(id=model.id, action='trainer_download_s3url')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, httplib.OK)
        resp_obj = json.loads(resp.data)
        self.assertEqual(resp_obj['trainer_file_for'], model.id)
        trainer_url = resp_obj['url']
        trainer_filename = model.get_trainer_filename()
        self.assertTrue(trainer_filename)
        self.assertTrue(
            's3.amazonaws.com/%s?Signature' % trainer_filename in trainer_url)
        self.assertTrue(trainer_url.startswith('https://'))

        # trainer file not yet uploaoded
        model = Model.query.filter_by(name='OtherModel').first()
        self.assertTrue(model)
        url = self._get_url(id=model.id, action='trainer_download_s3url')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, httplib.OK)
        resp_obj = json.loads(resp.data)
        self.assertEqual(resp_obj['trainer_file_for'], model.id)
        self.assertTrue(resp_obj['url'] is None)

        # not trained
        model = Model.query.filter_by(name='NewModel').first()
        self.assertTrue(model)
        url = self._get_url(id=model.id, action='trainer_download_s3url')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, httplib.OK)
        resp_obj = json.loads(resp.data)
        self.assertEqual(resp_obj['trainer_file_for'], model.id)
        self.assertTrue(resp_obj['url'] is None)

    """
    POST
    """

    @mock_s3
    def test_post_validation(self, *mocks):
        # No name
        self.check_edit_error(
            {
                'test_import_handler': self.handler.id,
                'import_handler': self.handler.id,
            },
            {'name': 'name is required'})

        # Invalid features
        post_data = {'test_import_handler_file': EXTRACT_XML,
                     'import_handler_file': EXTRACT_XML,
                     'features': 'smth',
                     'name': 'new'}
        self.check_edit_error(
            post_data,
            {'features': 'JSON file is corrupted. Can not load it: smth'})

        post_data = {'test_import_handler_file': EXTRACT_XML,
                     'import_handler_file': EXTRACT_XML,
                     'features': '{"a": "1"}',
                     'name': 'new'}
        self.check_edit_error(
            post_data,
            {'features': "Features JSON file is invalid: "
                         "schema-name is missing"})

        # Invalid trainer
        post_data = {'test_import_handler_file': EXTRACT_XML,
                     'import_handler_file': EXTRACT_XML,
                     'trainer': INVALID_MODEL,
                     'name': 'new'}
        self.check_edit_error(post_data, {
            'trainer': "Pickled trainer model is invalid: "
                       "No module named core.trainer.store"
        })

    def test_post(self):
        # No features specified
        resp, model = self._test_post(fill_import_handler=True)
        self.assertEquals(model.feature_count, 0)
        self.assertFalse(model.target_variable)
        self.assertTrue(model.features_set, "Features set not created")
        self.assertFalse(
            Feature.query.filter_by(feature_set=model.features_set).count())

        # Features are specified
        self._test_post(fill_import_handler=True, fill_features=True)

        # Import handler from file
        data = {'import_handler_file': EXTRACT_XML}
        resp, model = self._test_post(extra_data=data, fill_features=True)
        self.assertTrue(model.test_import_handler)
        self.assertTrue(model.train_import_handler)
        self.assertEquals(model.train_import_handler.id,
                          model.train_import_handler.id)

        # Different import handlers
        data = {'test_import_handler_file': EXTRACT_XML,
                'import_handler_file': EXTRACT_XML}
        resp, model = self._test_post(extra_data=data, fill_features=True)
        self.assertTrue(model.test_import_handler,
                        "Test import handler was not set")
        self.assertTrue(model.train_import_handler,
                        "Train import handler was not set")
        self.assertNotEquals(
            model.test_import_handler.id, model.train_import_handler.id)

        # Json import handler used
        handler = ImportHandler.query.first()
        data = {'import_handler': handler.identifier}
        resp, model = self._test_post(extra_data=data, fill_features=True)
        self.assertTrue(
            handler.id == model.train_import_handler.id ==
            model.test_import_handler.id)

        # Posting trained model
        self._test_post(fill_import_handler=True, fill_trainer=True)

    @patch('api.ml_models.models.Model.set_trainer')
    def test_post_with_errors(self, mock_set_trainer):
        """
        Checks whether nothing created, when exc. occures while adding models.
        """
        model_count = Model.query.count()
        ih_count = ImportHandler.query.count()
        mock_set_trainer.side_effect = Exception('My error in set_trainer')
        post_data = {'test_import_handler_file': EXTRACT_XML,
                     'import_handler_file': EXTRACT_XML,
                     'features': FEATURES_STR,
                     'name': 'name'}
        resp = self.client.post(
            self.BASE_URL, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 500)
        self.assertTrue(mock_set_trainer.called)
        self.assertEquals(model_count, Model.query.count())
        self.assertEquals(ih_count, ImportHandler.query.count())

    @mock_s3
    def test_clone_the_model(self):
        self.obj.tags = [Tag.query.first()]
        old_tag_count = self.obj.tags[0].count
        self.obj.save()
        resp_data = self._check(
            method='post', data={}, id=self.obj.id, action="clone")
        cloned_model = Model.query.get(resp_data['model']['id'])
        self.assertEquals(
            cloned_model.train_import_handler, self.obj.train_import_handler)
        self.assertEquals(
            cloned_model.test_import_handler, self.obj.test_import_handler)
        self.assertEquals(cloned_model.classifier, self.obj.classifier)
        self.assertItemsEqual(cloned_model.tags, self.obj.tags)
        # TODO:
        # self.assertEquals(cloned_model.tags[0].count, old_tag_count + 1)

    ############
    # Test PUT #
    ############

    def test_edit_model(self):
        # TODO: Add validation to importhandlers
        data = {'name': 'new name',
                'example_id': 'some_id',
                'example_label': 'some_label', }
        data, model = self.check_edit(data, id=self.obj.id)
        self.assertEquals(data['model']['name'], model.name)
        self.assertEquals(model.example_id, 'some_id')
        self.assertEquals(model.example_label, 'some_label')

    def test_edit_model_name(self):
        data = {'name': 'new name %@#'}
        data, model = self.check_edit(data, id=self.obj.id)
        self.assertTrue(model.name == data['model']['name'] ==
                        'new name %@#')

    def test_edit_tags(self):
        self.obj.tags = []
        self.obj.save()

        data = {'tags': json.dumps(['tag'])}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals([t.text for t in obj.tags], ['tag'])

        tag = Tag.query.filter_by(text='tag').one()
        self.assertEquals(tag.count, 1)

        data = {'tags': json.dumps(['tag', 'tag2'])}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertItemsEqual([t.text for t in obj.tags], ['tag', 'tag2'])

        model2 = Model.query.filter_by(name=ModelData.model_02.name).first()
        data = {'tags': json.dumps(['tag'])}
        resp, obj = self.check_edit(data, id=model2.id)
        self.assertEquals([t.text for t in obj.tags], ['tag'])

        tag = Tag.query.filter_by(text='tag').one()
        self.assertEquals(tag.count, 2)

        tag2 = Tag.query.filter_by(text='tag2').one()
        self.assertEquals(tag2.count, 1)

        data = {'tags': json.dumps(['tag2', 'some_new'])}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self. assertItemsEqual(
            [t.text for t in obj.tags], ['tag2', 'some_new'])

        tag = Tag.query.filter_by(text='tag').one()
        self.assertEquals(tag.count, 1)

        tag2 = Tag.query.filter_by(text='tag2').one()
        self.assertEquals(tag2.count, 1)

        tag3 = Tag.query.filter_by(text='some_new').one()
        self.assertEquals(tag3.count, 1)

    @mock_s3
    @patch('api.servers.tasks.upload_model_to_server')
    def test_upload_to_server(self, mock_task):
        url = self._get_url(id=self.obj.id, action='upload_to_server')
        server = Server.query.filter_by(name=ServerData.server_01.name).one()

        resp = self.client.put(url, data={'server': server.id},
                               headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(mock_task.delay.called)
        self.assertTrue('status' in json.loads(resp.data))

        self.obj.status = Model.STATUS_NEW
        self.obj.save()

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

    """
    Testing model training.
    """

    @mock_s3
    def test_train_model_validation_errors(self, *mocks):
        self.assertTrue(self.obj.status, Model.STATUS_NEW)
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        data = {
            'existing_instance_selected': True,
            'new_dataset_selected': True,
            'params': '{}'
        }
        self.check_edit_error(
            data,
            {'aws_instance': 'Please select instance with a worker',
             'parameters': 'Some parameters are missing: start, end',
             'format': 'Please select format of the Data Set'},
            id=self.obj.id, action='train')

        data = {
            'existing_instance_selected': False,
            'new_dataset_selected': False
        }
        self.check_edit_error(data, {
            u'spot_instance_type': u'Please select Spot instance type',
            u'dataset': u'Please select Data Set'},
            id=self.obj.id, action='train')

        # Tests specifying dataset
        data = {
            'dataset': "11999,786",
            'existing_instance_selected': True,
            'new_dataset_selected': False,
            'aws_instance': self.instance.id,
        }
        self.check_edit_error(data, {
            'dataset': 'DataSet not found',
        }, id=self.obj.id, action='train')

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    @patch('cloudml.trainer.trainer.Trainer.__init__')
    def test_train_model_exception(self, mock_trainer,
                                   mock_get_features_json, *mocks):
        mock_trainer.side_effect = Exception('Some message')
        mock_get_features_json.return_value = FEATURES_STR

        ds = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': False,
                'dataset': ds.id}
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        self.assertEqual(obj.status, obj.STATUS_ERROR)
        self.assertEqual(obj.error, 'Some message')

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_dataset(self, mock_get_features_json, *mocks):
        mock_get_features_json.return_value = FEATURES_STR

        ds = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': False,
                'dataset': ds.id}
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds.name])

        self.assertEqual(obj.trained_by.uid, 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 100)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_dataset_csv(self, mock_get_features_json,
                                          *mocks):
        mock_get_features_json.return_value = FEATURES_STR

        ds = DataSet.query.filter_by(name=DataSetData.dataset_03.name).first()
        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': False,
                'dataset': ds.id}
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds.name])

        self.assertEqual(obj.trained_by.uid, 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 100)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_dataset_other_handler(self,
                                                    mock_get_features_json,
                                                    *mocks):
        mock_get_features_json.return_value = FEATURES_STR

        # Dataset from another handler
        new_handler = ImportHandler()
        new_handler.name = 'New Hnadler for the only one test'
        # new_handler.type = ImportHandler.TYPE_DB
        new_handler.import_params = ['start', 'end', 'category']
        new_handler.data = self.handler.data
        new_handler.save()
        ds = DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()
        ds.import_handler_id = new_handler.id
        ds.import_handler_type = new_handler.TYPE
        ds.save()

        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': False,
                'dataset': ds.id}
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds.name])

        self.assertEqual(obj.trained_by.uid, 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 100)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_datasets(self, mock_get_features_json, *mocks):
        mock_get_features_json.return_value = FEATURES_STR

        ds1 = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        ds2 = DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()

        data = {
            'aws_instance': self.instance.id,
            'existing_instance_selected': True,
            'new_dataset_selected': False,
            'dataset': ','.join([str(ds1.id), str(ds2.id)])
        }
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds1.name, ds2.name])

        self.assertEqual(obj.trained_by.uid, 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 200)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_without_dataset(
            self, mock_get_features_json, *mocks):
        mock_get_features_json.return_value = FEATURES_STR
        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': 1,
                'new_dataset_selected': 1,
                'parameters': TRAIN_PARAMS,
                'format': DataSet.FORMAT_JSON}
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertIsInstance(obj.datasets[0].id, int)
        self.assertEquals(obj.dataset.format, DataSet.FORMAT_JSON)
        self.assertEqual(obj.trained_by.uid, 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 99)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_load_params_csv(self, mock_get_features_json,
                                              *mocks):
        mock_get_features_json.return_value = FEATURES_STR

        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': True,
                'parameters': TRAIN_PARAMS,
                'format': DataSet.FORMAT_CSV
                }
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertIsInstance(obj.datasets[0].id, int)
        self.assertEquals(obj.dataset.format, DataSet.FORMAT_CSV)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    def test_retrain_model(self, mock_load_key,
                           mock_multipart_upload, mock_get_features_json):
        self.assertTrue(self.obj.train_import_handler,
                        "Train import handler should be filled")

        mock_get_features_json.return_value = FEATURES_STR
        mock_load_key.return_value = MODEL_TRAINER

        self.obj.status = Model.STATUS_TRAINED
        self.obj.save()

        from api.model_tests.models import TestResult, TestExample
        test1 = TestResult.query.filter_by(
            name=TestResultData.test_01.name).first()
        test1.model = self.obj
        test1.save()
        test1_id = test1.id

        example1 = TestExample.query.filter_by(
            name=TestExampleData.test_example_01.name).first()
        example1.test_result = test1
        example1.model = self.obj
        example1.save()
        example1_id = example1.id

        example2 = TestExample.query.filter_by(
            name=TestExampleData.test_example_02.name).first()
        example2.test_result = test1
        example2.model = self.obj
        example2.save()
        example2_id = example2.id

        data = {'aws_instance': self.instance.id,
                'existing_instance_selected': True,
                'new_dataset_selected': True,
                'parameters': TRAIN_PARAMS,
                'format': DataSet.FORMAT_CSV
                }
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')

        self.assertIsNone(TestResult.query.filter_by(id=test1_id).first())
        self.assertIsNone(TestExample.query.filter_by(id=example1_id).first())
        self.assertIsNone(TestExample.query.filter_by(id=example2_id).first())
        self.assertEquals(obj.status, 'Trained', obj.error)

        # Checking weights
        self.assertTrue(obj.weights_synchronized)
        tr_weights = self.obj.get_trainer(force_load=True).get_weights()
        pos_count = len(tr_weights[1]['positive'])
        neg_count = len(tr_weights[1]['negative'])
        valid_count = pos_count + neg_count
        weights = obj.weights

        self.assertEquals(len(weights), valid_count)
        categories = obj.weight_categories
        self.assertEquals(len(categories), 4)

    @mock_s3
    @patch('api.instances.tasks.cancel_request_spot_instance')
    def test_cancel_request_instance(self, mock_task, *mocks):
        url = self._get_url(id=self.obj.id, action='cancel_request_instance')

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertFalse(mock_task.delay.called)

        self.obj.status = self.obj.STATUS_REQUESTING_INSTANCE
        self.obj.spot_instance_request_id = 'someid'
        self.obj.save()

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(mock_task.delay.called)

    @patch('api.ml_models.tasks.transform_dataset_for_download')
    def test_put_dataset_download_action(self, transform_mock):
        dataset = DataSet.query.filter_by(
            name=DataSetData.dataset_01.name).first()

        # bogus model
        self.obj.status = Model.STATUS_TRAINING
        url = self._get_url(id=101010,
                            action='dataset_download')
        resp = self.client.put(url, headers=HTTP_HEADERS,
                               data={'dataset': dataset.id})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)

        # model not trained
        self.obj.status = Model.STATUS_TRAINING
        url = self._get_url(id=self.obj.id,
                            action='dataset_download')
        resp = self.client.put(url, headers=HTTP_HEADERS,
                               data={'dataset': dataset.id})
        self.assertEquals(resp.status_code, 400)

        # model is trained
        self.obj.status = Model.STATUS_TRAINED
        url = self._get_url(id=self.obj.id,
                            action='dataset_download')
        resp = self.client.put(url, headers=HTTP_HEADERS,
                               data={'dataset': dataset.id})
        self.assertEquals(resp.status_code, httplib.OK)

        transform_mock.delay.assert_called_with(self.obj.id, dataset.id)

    @patch('api.ml_models.views.AsyncTask.get_current_by_object')
    def test_get_dataset_download_action(self, async_get_object_mock):
        # bogus model
        url = self._get_url(id=101010,
                            action='dataset_download')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)

        # existing model
        dataset = DataSet.query.filter_by(
            name=DataSetData.dataset_01.name).first()
        from api.async_tasks.models import AsyncTask
        task = AsyncTask()
        task.args = [self.obj.id, dataset.id]
        task.object_id = self.obj.id
        async_get_object_mock.return_value = [task]
        self.obj.status = Model.STATUS_TRAINING
        url = self._get_url(id=self.obj.id,
                            action='dataset_download')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        resp_obj = json.loads(resp.data)
        self.assertEqual(async_get_object_mock.call_args_list[0][0][1],
                         'api.ml_models.tasks.transform_dataset_for_download')
        self.assertTrue('downloads' in resp_obj)
        self.assertEqual(resp_obj['downloads'][0]['dataset']['id'], dataset.id)

    def test_put_add_features_from_xml_ih_action(self):
        # bogus model
        url = self._get_url(id=101010,
                            action='dataset_download')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)

        # model is trained
        model = Model.query.filter_by(name=ModelData.model_01.name).first()

        url = self._get_url(id=model.id, action='import_features_from_xml_ih')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 400)

        # new model but trainer is not xml
        model = Model.query.filter_by(name=ModelData.model_03.name).first()
        url = self._get_url(id=model.id, action='import_features_from_xml_ih')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 400)

        # new model, trainer xml but feature count is not 0
        model = Model.query.filter_by(name=ModelData.model_04.name).first()
        url = self._get_url(id=model.id, action='import_features_from_xml_ih')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 400)

        # new model, trainer xml feature count is 0
        xml_ih = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        model = Model.query.filter_by(name=ModelData.model_05.name).first()
        model.train_import_handler_id = xml_ih.id
        model.save()

        url = self._get_url(id=model.id, action='import_features_from_xml_ih')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        resp_obj = json.loads(resp.data)
        self.assertEqual(resp_obj['model'], model.id)
        self.assertEqual(len(resp_obj['features']), 2)
        self.assertEqual(resp_obj['features'][0]['name'], 'opening_id')
        self.assertEqual(resp_obj['features'][0]['type'], 'int')

    @mock_s3
    def _test_post(self, name=None, extra_data=None,
                   fill_import_handler=False, fill_features=False,
                   fill_trainer=False, *mocks):
        data = {}
        if extra_data is not None:
            data.update(extra_data)
        if name is None:
            import uuid
            name = str(uuid.uuid1())
        if fill_import_handler:
            import_handler = ImportHandler.query.first()
            data['import_handler'] = import_handler.identifier
        if fill_features:
            data['features'] = FEATURES_STR
        if fill_trainer:
            data['trainer'] = MODEL_TRAINER
        data['name'] = name

        logging.debug('Posting model with filled: {0}'.format(data.keys()))
        resp, model = self.check_edit(data)
        self.assertEquals(model.name, name)

        if fill_import_handler:
            self.assertEquals(model.test_import_handler, import_handler)
            self.assertEquals(model.train_import_handler, import_handler)
            self.assertTrue(
                import_handler.id == model.train_import_handler.id ==
                model.train_import_handler.id)
        if fill_features:
            self._check_features_from_conf(model)
        if fill_trainer:
            # Checking trained model
            self.assertEquals(model.status, model.STATUS_TRAINED)
            self.assertEquals(model.labels, ['0', '1'])
        else:
            self.assertEquals(model.status, model.STATUS_NEW)
            self.assertEquals(model.labels, [],
                              "Labels is empty for recently posted model")
        self.assertFalse(model.dataset)
        self.assertFalse(model.example_id)
        self.assertFalse(model.example_label)
        self.assertFalse(model.comparable)
        self.assertEquals(model.tags, [])
        self.assertFalse(model.error)
        self.assertEquals(model.weights_synchronized, fill_trainer)

        return resp, model

    def _check_features_from_conf(self, model):
        """
        Checks whether features correctly loaded from conf/features.json file
        """
        self.assertEquals(model.feature_count, FEATURE_COUNT)
        self.assertEquals(model.target_variable, TARGET_VARIABLE)
        features = Feature.query.filter_by(feature_set=model.features_set)
        self.assertEquals(features.count(), 37)

        # Checking that classifier from features created
        classifier = model.classifier
        self.assertTrue(classifier, "classifier not setted")
        self.assertEquals(classifier['type'], u'logistic regression')
        self.assertEquals(classifier['params'], {u'penalty': u'l2'})

        # Checking that features set created
        features_set = model.features_set
        self.assertTrue(features_set, "Features set not created")
        self.assertEquals(features_set.schema_name, "bestmatch")

        for feature in features:
            self.assertTrue(feature.name)
            self.assertTrue(feature.type)
