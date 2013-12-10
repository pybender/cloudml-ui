import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import TestsResource, TestExamplesResource
from models import TestResult, TestExample
from api.ml_models.models import Model, Weight
from api.ml_models.fixtures import ModelData, WeightData
from api.import_handlers.fixtures import ImportHandlerData, DataSetData
from api.import_handlers.models import DataSet, ImportHandler
from api.instances.models import Instance
from api.instances.fixtures import InstanceData
from fixtures import TestResultData, TestExampleData


class TestTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Test API.
    """
    BASE_URL = '/cloudml/models/{0!s}/tests/'
    RESOURCE = TestsResource
    Model = TestResult
    datasets = [InstanceData, ImportHandlerData, DataSetData,
                ModelData, TestResultData]

    def setUp(self):
        super(TestTests, self).setUp()
        self.obj = self.Model.query.filter_by(
            name=TestResultData.test_01.name).one()

        self.model = Model.query.filter_by(
            name=ModelData.model_01.name).first()
        handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        self.model.train_import_handler = handler
        self.model.test_import_handler = handler
        self.model.save()

        self.obj.model = self.model
        self.obj.save()

        self.BASE_URL = self.BASE_URL.format(self.obj.model.id)
        self.MODEL_PARAMS = {'model_id': self.obj.model.id}
        self.RELATED_PARAMS = {'test_result_id': self.obj.id,
                               'model_id': self.obj.model.id}
        self.instance = Instance.query.filter_by(
            name=InstanceData.instance_01.name).one()
        self.POST_DATA = {'aws_instance': self.instance.id}

    def test_list(self):
        self.check_list(show='', query_params=self.MODEL_PARAMS)
        self.check_list(show='name,status', query_params=self.MODEL_PARAMS)

    def test_details(self):
        self.check_details(show='')
        self.check_details(show='name,status')

    @patch('api.tasks.calculate_confusion_matrix')
    def test_confusion_matrix(self, mock_calculate):
        url = self._get_url(
            id=self.obj.id,
            action='confusion_matrix',
            weight0=10,
            weight1=12,
        )
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        mock_calculate.delay.assert_called_once_with(
            self.obj.id,
            10.0,
            12.0
        )

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.tasks.run_test')
    def test_post(self, mock_run_test, mock_multipart_upload):
        """
        Checks creating new Test with creating new dataset.
        """
        data = {
            'format': DataSet.FORMAT_JSON
        }
        import_params = {'start': '2012-12-03',
                         'end': '2012-12-04',
                         'category': 'smth'}
        data.update(self.POST_DATA)
        data.update(import_params)
        data, test = self.check_edit(data, load_json=True)

        self.assertEquals(test.status, test.STATUS_IMPORTED)
        self.assertTrue(test.name.startswith('Test'))
        model = self.model
        self.assertEquals(test.model_name, model.name)
        self.assertEquals(test.model, model)
        self.assertEquals(test.model_id, model.id)
        self.assertFalse(test.error)
        self.assertTrue(test.created_on)
        # TODO
        # self.assertEquals(test.created_by['name'], 'User-1')
        self.assertEquals(test.parameters, import_params)

        # This info should be filled after completing running
        # run_test celery task, which is mocked
        self.assertFalse(test.examples_count)
        self.assertFalse(test.accuracy)
        self.assertFalse(test.classes_set)
        self.assertFalse(test.metrics)
        self.assertFalse(test.dataset)
        self.assertFalse(test.memory_usage)

        self.assertTrue(mock_multipart_upload.called,
                        'Loaded dataset should be uploaded to Amazon S3')

        instance = self.instance
        mock_run_test.subtask.assert_called_once_with(
            args=(test.id, ),
            options={'queue': instance.name})
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['id'], test.id)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['name'], test.name)

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.tasks.run_test')
    def test_post_csv(self, mock_run_test, mock_multipart_upload):
        """
        Checks creating new Test with creating new dataset.
        """
        data = {
            'format': DataSet.FORMAT_CSV
        }
        import_params = {'start': '2012-12-03',
                         'end': '2012-12-04',
                         'category': 'smth'}
        data.update(self.POST_DATA)
        data.update(import_params)
        resp, test = self.check_edit(data)

        self.assertEquals(test.status, test.STATUS_IMPORTED)
        self.assertTrue(test.name.startswith('Test'))
        model = self.model
        self.assertEquals(test.model_name, model.name)
        self.assertEquals(test.model, model)
        self.assertEquals(test.model_id, self.model.id)
        self.assertFalse(test.error)

    @mock_s3
    @patch('api.tasks.run_test')
    def test_post_with_dataset(self, mock_run_test):
        """
        Tests creating new Test with specifying dataset.
        """
        dataset = DataSet.query.filter_by(
            name=DataSetData.dataset_01.name).first()
        data = {'dataset': dataset.id}
        data.update(self.POST_DATA)
        resp = self.client.post(self._get_url(), data=data,
                                headers=HTTP_HEADERS)
        data = json.loads(resp.data)
        self.assertEquals(resp.status_code, 201)

        test = TestResult.query.get(data[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEquals(test.status, test.STATUS_QUEUED)

        instance = Instance.query.get(self.instance.id)
        mock_run_test.apply_async.assert_called_once_with(
            ([dataset.id], test.id),
            queue=instance.name)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in data)

    def test_post_validation(self):
        """
        Tests validation errors, when posting new Test.
        """
        def _check(post_data, errors=None):
            resp = self.client.post(self._get_url(), data=post_data,
                                 headers=HTTP_HEADERS)
            data = json.loads(resp.data)
            self.assertEquals(resp.status_code, 400)
            if errors:
                err_list = data['response']['error']['errors']
                errors_dict = dict([(item['name'], item['error'])
                                    for item in err_list])
                for field, err_msg in errors.iteritems():
                    self.assertTrue(field in errors_dict,
                                    "Should be err for field %s: %s" % (field, err_msg))
                    self.assertEquals(err_msg, errors_dict[field])
                self.assertEquals(len(errors_dict), len(errors),
                                  errors_dict.keys())

        data = {}
        errors = {
            'fields': u'One of spot_instance_type, aws_instance is required. \
One of parameters, dataset is required.'}
        _check(data, errors)

        data = {'aws_instance': self.instance.id}
        errors = {
            'fields': 'One of parameters, dataset is required.'}
        _check(data, errors)

        data = {'aws_instance': 582,
                'dataset': 376}
        errors = {
            'aws_instance': u'Instance not found',
            'dataset': 'DataSet not found'}
        _check(data, errors)

        data = {'spot_instance_type': 'INVALID',
                'start': '2013-01-01'}
        errors = {
            'spot_instance_type': "Should be one of m3.xlarge, m3.2xlarge,"
                                  " cc2.8xlarge, cr1.8xlarge,"
                                  " hi1.4xlarge, hs1.8xlarge",
            'parameters': 'Parameters category, end are required',
            'fields': 'One of parameters, dataset is required.'  # TODO: Remove.
        }
        _check(data, errors)

        # TODO
#     def test_delete(self):
#         # self.check_related_docs_existance(self.db.TestExample)
#         self.check_delete()
#
# #         self.check_related_docs_existance(self.db.TestExample, exist=False,
# #                                           msg='Tests Examples should be \
# # when remove test')
#
#         # Checks whether not all docs was deleted
#         self.assertTrue(TestResult.query.count(),
#                         "All tests was deleted!")
#         self.assertTrue(TestExample.query.count(),
#                         "All examples was deleted!")


class TestExamplesTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Test Examples API.
    """
    RESOURCE = TestExamplesResource
    Model = TestExample
    datasets = [ImportHandlerData, DataSetData, ModelData, WeightData,
                TestResultData, TestExampleData]

    def setUp(self):
        super(TestExamplesTests, self).setUp()
        self.test = TestResult.query.filter_by(
            name=TestResultData.test_01.name).first()
        self.model = self.test.model

        for w in Weight.query.all():
            w.model = self.model
            w.save()

        for ex in TestExample.query.all():
            ex.test_result = self.test
            ex.save()
        self.obj = self.test.examples[0]

        self.obj.model = self.model
        self.obj.save()

        self.test.model = self.model
        self.test.save()

        self.BASE_URL = '/cloudml/models/{0!s}/tests/{1!s}/examples/'.format(
            self.model.id, self.test.id
        )

    def test_list(self):
        self.check_list(show='created_on,label,pred_label')

        url = '{0}?{1}&{2}'.format(
            self.BASE_URL,
            'action=examples:list',
            'data_input.employer->country=United Kingdom'
        )
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)

    @mock_s3
    @patch('api.model_tests.models.TestResult.get_vect_data')
    @patch('api.ml_models.models.Model.get_trainer')
    def test_details_weight(self, mock_get_trainer, mock_get_vect_data):
        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(
            open('api/ml_models/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        mock_get_vect_data.return_value = [0.123, 0.0] * 500

        url = self._get_url(id=self.obj.id, show='id,name,weighted_data_input')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_trainer.called)
        data = json.loads(resp.data)['test_examples']

        for key in ['css_class', 'model_weight', 'transformed_weight',
                    'value', 'vect_value', 'weight']:
            self.assertTrue(key in data['weighted_data_input']['opening_id'])

    def test_groupped(self):
        for ex in TestExample.query.all():
            ex.test_result = self.test
            ex.save()

        url = self._get_url(action='groupped',
                            field='opening_id', count='2')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEquals(data['field_name'], 'opening_id')
        item = data['test_exampless']['items'][0]
        self.assertEquals(item['count'], 5)
        self.assertEquals(item['group_by_field'], '201913099')
        self.assertTrue(item['avp'] > 0)
        self.assertTrue(data['mavp'] > 0)

    def test_datafields(self):
        url = self._get_url(action='datafields')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEquals(data['fields'], ['employer->country'])

    @patch('api.tasks.get_csv_results')
    def test_csv(self, mock_get_csv):
        fields = 'name,id,label,pred_label,prob,data_input.employer->country'
        url = self._get_url(action='csv', show=fields)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_csv.delay.called)
