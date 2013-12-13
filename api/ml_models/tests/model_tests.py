import httplib
import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS, FEATURE_COUNT, TARGET_VARIABLE
from ..views import ModelResource
from ..models import Model, Tag, db
from ..fixtures import ModelData
from api.import_handlers.fixtures import ImportHandlerData, DataSetData
from api.import_handlers.models import DataSet, ImportHandler
from api.instances.models import Instance
from api.instances.fixtures import InstanceData
from api.model_tests.models import TestResult, TestExample
from api.model_tests.fixtures import TestResultData, TestExampleData


class ModelsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Model API.
    """
    BASE_URL = '/cloudml/models/'
    RESOURCE = ModelResource
    Model = Model
    datasets = [ImportHandlerData, DataSetData, ModelData,
                 InstanceData, TestResultData, TestExampleData]

    def setUp(self):
        super(ModelsTests, self).setUp()
        self.obj = Model.query.filter_by(
            name=ModelData.model_01.name).first()
        self.handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        self.instance = Instance.query.filter_by(
            name=InstanceData.instance_01.name).first()

        self.obj.test_import_handler = self.handler
        self.obj.train_import_handler = self.handler
        self.obj.save()

    def test_list(self):
        self.check_list(show='')
        self.check_list(show='created_on,updated_on,name')

    def test_filter(self):
        self.check_list(data={'status': 'New'}, query_params={'status': 'New'})
        # No name filter - all models should be returned
        self.check_list(data={'name': 'Test'}, query_params={})

        # Comparable filter
        #self.check_list(data={'comparable': '1'}, query_params={'comparable': True})
        #self.check_list(data={'comparable': '0'}, query_params={'comparable': False})

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
        self.assertEquals(resp['model']['data_fields'], ['employer.country'])

    def test_download(self):
        def check(field, is_invalid=False):
            url = self._get_url(id=self.obj.id, action='download',
                                field=field)
            resp = self.client.get(url, headers=HTTP_HEADERS)
            if not is_invalid:
                self.assertEquals(resp.status_code, httplib.OK)
                self.assertEquals(resp.mimetype, 'text/plain')
                self.assertEquals(resp.headers['Content-Disposition'],
                                  'attachment; filename=%s-%s.json' %
                                  (self.obj.name, field))
            else:
                self.assertEquals(resp.status_code, 400)
        check('features')
        check('invalid', is_invalid=True)

    def test_post_without_name(self):
        self.check_edit_error(
            {
                'test_import_handler': self.handler.id,
                'train_import_handler': self.handler.id,
            },
            {'name': 'name is required'})

    def test_post_with_invalid_features(self):
        # Features aren't required. Can be added in model details
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'features': 'smth',
                     'name': 'new'}
        self.check_edit_error(
            post_data,
            {'features': 'invalid json: smth'})

        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'features': '{"a": "1"}',
                     'name': 'new'}
        self.check_edit_error(
            post_data,
            {'features': 'Invalid features: schema-name is missing'})

    def test_post_with_invalid_trainer(self):
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('api/ml_models/invalid_model.dat', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'trainer': trainer,
                     'name': 'new'}
        self.check_edit_error(post_data, {
            'trainer': "Invalid trainer: Could not unpickle trainer - 'module' object has no attribute 'TrainerStorage1'"
        })

    def test_post_new_model(self, name='new'):
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'features': open('./conf/features.json', 'r').read(),
                     'name': name}
        resp, model = self.check_edit(post_data)
        self.assertEquals(model.name, name)
        self.assertEquals(model.status, model.STATUS_NEW)
        self.assertTrue(model.test_import_handler,
                        "Test import handler was not set")
        self.assertTrue(model.train_import_handler,
                        "Train import handler was not set")
        # TODO
        # self.assertTrue(model.features, "Features was not set")
        self.assertEquals(model.labels, [],
                          "Labels is empty for recently posted model")
        self.assertFalse(model.dataset)
        self.assertEquals(model.feature_count, FEATURE_COUNT)
        self.assertEquals(model.target_variable, TARGET_VARIABLE)
        self.assertFalse(model.example_id)
        self.assertFalse(model.example_label)
        self.assertFalse(model.comparable)
        self.assertEquals(model.tags, [])
        self.assertFalse(model.weights_synchronized)
        self.assertFalse(model.error)

        # Checking that classifier from features created
        classifier = model.classifier
        self.assertTrue(classifier, "classifier not setted")
        self.assertEquals(classifier['type'], u'logistic regression')
        self.assertEquals(classifier['params'], {u'penalty': u'l2'})

        # Checking that features set created
        features_set = model.features_set
        self.assertTrue(features_set, "Features set not created")
        self.assertEquals(features_set.schema_name, "bestmatch")

    def test_post_new_model_without_features(self):
        """
        User could create new model without specifying features
        and then start adding them using UI.
        """
        name = 'test one'
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'name': name}
        resp, model = self.check_edit(post_data)
        self.assertEquals(model.name, name)
        self.assertEquals(model.status, model.STATUS_NEW)
        
        features_set = model.features_set
        self.assertTrue(features_set, "Features set not created")

    def test_post_trained_model(self):
        # TODO: what to do with features here?
        name = 'new2'
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/ml_models/model.dat', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'trainer': trainer,
                     'name': name}
        resp, model = self.check_edit(post_data)
        self.assertEquals(model.name, name)
        self.assertEquals(model.status, model.STATUS_TRAINED)
        self.assertTrue(model.trainer.read())

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
        self.assertEquals(set([t.text for t in obj.tags]), set(['tag', 'tag2']))

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
        self.assertEquals(set([t.text for t in obj.tags]), set(['tag2', 'some_new']))

        tag = Tag.query.filter_by(text='tag').one()
        self.assertEquals(tag.count, 1)

        tag2 = Tag.query.filter_by(text='tag2').one()
        self.assertEquals(tag2.count, 1)

        tag3 = Tag.query.filter_by(text='some_new').one()
        self.assertEquals(tag3.count, 1)

    def test_train_model_validation_errors(self):
        self.assertTrue(self.obj.status, Model.STATUS_NEW)
        self.check_edit_error({}, {
            'fields': 'One of spot_instance_type, aws_instance is required.'
                      ' One of parameters, dataset is required.'
        }, id=self.obj.id, action='train')

        data = {
            'aws_instance': self.instance.id,
            'start': '2012-12-03',
            'format': DataSet.FORMAT_JSON
        }
        self.check_edit_error(data, {
            'parameters': 'Parameters category, end are required',
            'fields': 'One of parameters, dataset is required.'
        }, id=self.obj.id, action='train')

        data = {
            'aws_instance': self.instance.id,
            'format': DataSet.FORMAT_JSON
        }
        self.check_edit_error(data, {
            'fields': 'One of parameters, dataset is required.'
        }, id=self.obj.id, action='train')

        # Tests specifying dataset
        data = {
            'dataset': 786,
            'aws_instance': self.instance.id,
        }
        self.check_edit_error(data, {
            'dataset': 'DataSet not found',
        }, id=self.obj.id, action='train')

    @patch('api.ml_models.models.Model.get_features_json')
    @patch('core.trainer.trainer.Trainer.__init__')
    def test_train_model_exception(self, mock_trainer, mock_get_features_json):
        mock_trainer.side_effect = Exception('Some message')
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        ds = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        data = {'aws_instance': self.instance.id,
                'dataset': ds.id}

        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        self.assertEqual(obj.status, obj.STATUS_ERROR)
        self.assertEqual(obj.error, 'Some message')

    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_dataset(self, mock_get_features_json):
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        ds = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        data = {'aws_instance': self.instance.id,
                'dataset': ds.id}
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds.name])

        self.assertEqual(obj.trained_by['uid'], 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 100)

    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_dataset_csv(self, mock_get_features_json):
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        ds = DataSet.query.filter_by(name=DataSetData.dataset_03.name).first()
        data = {'aws_instance': self.instance.id,
                'dataset': ds.id}
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds.name])

        self.assertEqual(obj.trained_by['uid'], 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 100)

    # TODO
    def test_train_model_with_dataset_other_handler(self):
        pass

    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_dataset(self, mock_get_features_json):
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        ds1 = DataSet.query.filter_by(name=DataSetData.dataset_01.name).first()
        ds2 = DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()

        data = {
            'aws_instance': self.instance.id,
            'dataset': ','.join([str(ds1.id), str(ds2.id)])
        }
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        # NOTE: Make sure that ds.gz file exist in test_data folder

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertEqual([d.name for d in obj.datasets], [ds1.name, ds2.name])

        self.assertEqual(obj.trained_by['uid'], 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 200)

    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_load_params(self, mock_get_features_json):
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        data = {'aws_instance': self.instance.id,
                'start': '2012-12-03',
                'end': '2012-12-04',
                'category': '1',
                'format': DataSet.FORMAT_JSON
                }
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertIsInstance(obj.datasets[0].id, int)
        self.assertEquals(obj.dataset.format, DataSet.FORMAT_JSON)
        self.assertEqual(obj.trained_by['uid'], 'user')
        self.assertTrue(obj.memory_usage > 0)
        self.assertEqual(obj.train_records_count, 99)

    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_with_load_params_csv(self, mock_get_features_json):
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        data = {'aws_instance': self.instance.id,
                'start': '2012-12-03',
                'end': '2012-12-04',
                'category': '1',
                'format': DataSet.FORMAT_CSV
                }
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')

        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)
        self.assertIsInstance(obj.datasets[0].id, int)
        self.assertEquals(obj.dataset.format, DataSet.FORMAT_CSV)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_retrain_model(self, mock_multipart_upload, mock_get_features_json):
        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()

        self.obj.status = Model.STATUS_TRAINED
        self.obj.save()

        test1 = TestResult.query.filter_by(
            name=TestResultData.test_01.name).first()
        test1.model = self.obj
        test1.save()

        example1 = TestExample.query.filter_by(
            name=TestExampleData.test_example_01.name).first()
        example1.test_result = test1
        example1.model = self.obj
        example1.save()

        example2 = TestExample.query.filter_by(
            name=TestExampleData.test_example_02.name).first()
        example2.test_result = test1
        example2.model = self.obj
        example2.save()

        data = {'aws_instance': self.instance.id,
                'start': '2012-12-03',
                'end': '2012-12-04',
                'category': '1',
                'format': DataSet.FORMAT_CSV
                }
        resp, obj = self.check_edit(data, id=self.obj.id, action='train')
        self.assertEqual(obj.status, Model.STATUS_TRAINED, obj.error)

        self.assertIsNone(TestResult.query.filter_by(id=test1.id).first())
        self.assertIsNone(TestExample.query.filter_by(id=example1.id).first())
        self.assertIsNone(TestExample.query.filter_by(id=example2.id).first())

        # Checking weights
        self.assertTrue(obj.weights_synchronized)
        tr_weights = self.obj.get_trainer().get_weights()
        valid_count = len(tr_weights['positive']) + len(tr_weights['negative'])
        weights = obj.weights

        self.assertEquals(len(weights), valid_count)
        categories = obj.weight_categories
        self.assertEquals(len(categories), 6)

        self.assertEquals(obj.status, 'Trained')

    @patch('api.instances.tasks.cancel_request_spot_instance')
    def test_cancel_request_instance(self, mock_task):
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


# class TasksTests()  # TODO:
