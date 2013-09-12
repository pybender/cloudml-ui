import json
from mock import patch, MagicMock
from bson.objectid import ObjectId
from moto import mock_s3

from api import app
from utils import BaseTestCase, HTTP_HEADERS
from api.views import Tests as TestResource
from constants import INSTANCE_ID, DATASET_ID, MODEL_ID


class TestTests(BaseTestCase):
    TEST_ID = '000000000000000000000002'
    DS_ID = '5270dd3a106a6c1631000000'
    MODEL_PARAMS = {'model_id': MODEL_ID}
    RELATED_PARAMS = {'test_id': TEST_ID, 'model_id': MODEL_ID}
    RESOURCE = TestResource
    FIXTURES = ('datasets.json', 'importhandlers.json', 'models.json',
                'tests.json', 'examples.json', 'instances.json', )
    POST_DATA = {'aws_instance': INSTANCE_ID,
                 'examples_fields': 'employer->op_country_tz,hire_outcome',
                 'examples_placement': app.db.Test.EXAMPLES_TO_MONGO}

    def setUp(self):
        super(TestTests, self).setUp()
        self.model = self.db.Model.find_one({'_id': ObjectId(MODEL_ID)})
        self.assertTrue(self.model, 'Invalid fixtures: models')

        self.Model = self.db.Test
        self.obj = self.db.Test.find_one({
            '_id': ObjectId(self.TEST_ID)})
        self.assertTrue(self.obj, 'Invalid fixtures: tests')

        self.BASE_URL = '/cloudml/models/%s/tests/' % self.model._id

    def test_list(self):
        self._check_list(show='', query_params=self.MODEL_PARAMS)
        self._check_list(show='name,status', query_params=self.MODEL_PARAMS)

    def test_details(self):
        self._check_details(show='name,status')

    @patch('api.tasks.calculate_confusion_matrix')
    def test_confusion_matrix(self, mock_calculate):
        mock_calculate.return_value = [[1, 2], [3, 4]]

        url = self._get_url(id=self.obj._id,
                            action='confusion_matrix')
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        matrix = data['confusion_matrix']
        self.assertEquals(matrix[0], ['0', [1, 2]])
        self.assertEquals(matrix[1], ['1', [3, 4]])

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.tasks.run_test')
    def test_post(self, mock_run_test, mock_multipart_upload):
        """
        Checks creating new Test with creating new dataset.
        """
        data = {}
        import_params = {'start': '2012-12-03',
                         'end': '2012-12-04',
                         'category': 'smth'}
        data.update(self.POST_DATA)
        data.update(import_params)
        resp, test = self._check_post(data, load_model=True)
        data = json.loads(resp.data)

        self.assertEquals(test.status, test.STATUS_IMPORTED)
        self.assertEquals(test.name, 'Test4')
        model = app.db.Model.find_one({'_id': ObjectId(MODEL_ID)})
        self.assertEquals(test.model_name, model.name)
        self.assertEquals(test.model, model)
        self.assertEquals(test.model_id, MODEL_ID)
        self.assertFalse(test.error)
        self.assertTrue(test.created_on)
        self.assertEquals(test.created_by['name'], 'User-1')
        self.assertEquals(test.parameters, import_params)
        self.assertEquals(test.examples_fields,
                          [u'employer->op_country_tz', u'hire_outcome'])
        self.assertEquals(test.examples_placement,
                          self.POST_DATA['examples_placement'])

        # This info should be filled after completing running
        # run_test celery task, which is mocked
        self.assertFalse(test.examples_count)
        self.assertFalse(test.accuracy)
        self.assertFalse(test.classes_set)
        self.assertFalse(test.metrics)
        self.assertFalse(test.dataset)
        self.assertFalse(test.memory_usage)
        self.assertFalse(test.exports)

        self.assertTrue(mock_multipart_upload.called,
                        'Loaded dataset should be uploaded to Amazon S3')

        instance = app.db.Instance.find_one({'_id': ObjectId(INSTANCE_ID)})
        mock_run_test.subtask.assert_called_once_with(
            args=(str(test._id), ),
            options={'queue': instance.name})
        self.assertEquals(data['test']['_id'], str(test._id))
        self.assertEquals(data['test']['name'], str(test.name))

    @mock_s3
    @patch('api.tasks.run_test')
    def test_post_with_dataset(self, mock_run_test):
        """
        Tests creating new Test with specifying dataset.
        """
        data = {'dataset': DATASET_ID}
        data.update(self.POST_DATA)
        resp = self.app.post(self._get_url(), data=data, headers=HTTP_HEADERS)
        data = json.loads(resp.data)
        self.assertEquals(resp.status_code, 201)

        test = self.db.Test.get_from_id(ObjectId(data['test']['_id']))
        self.assertEquals(test.status, test.STATUS_QUEUED)

        instance = app.db.Instance.find_one({'_id': ObjectId(INSTANCE_ID)})
        mock_run_test.apply_async.assert_called_once_with(
            ([DATASET_ID], str(test._id)),
            queue=instance.name)
        self.assertTrue('test' in data)

    def test_post_validation(self):
        """
        Tests validation errors, when posting new Test.
        """
        def _check(post_data, errors=None):
            resp = self.app.post(self._get_url(), data=post_data,
                                 headers=HTTP_HEADERS)
            data = json.loads(resp.data)
            self.assertEquals(resp.status_code, 400)
            if errors:
                err_list = data['response']['error']['errors']
                errors_dict = dict([(item['name'], item['error'])
                                    for item in err_list])
                for field, err_msg in errors.iteritems():
                    self.assertEquals(err_msg, errors_dict[field])
                self.assertEquals(len(errors_dict), len(errors),
                                  errors_dict.keys())

        data = {}
        errors = {
            u'examples_fields': u'Examples fields are required',
            None: u'One of spot_instance_type, aws_instance is required. \
One of parameters, dataset is required.',
            u'examples_placement': u'Examples placement is required'}
        _check(data, errors)

        data = {'examples_fields': 'hire_outcome,application_id',
                'examples_placement': 'Invalid',
                'aws_instance': INSTANCE_ID}
        errors = {
            u'examples_placement': u'Invalid test examples storage specified',
            None: 'One of parameters, dataset is required.'}
        _check(data, errors)

        data = {'examples_fields': 'hire_outcome,application_id',
                'examples_placement': app.db.Test.EXAMPLES_TO_MONGO,
                'aws_instance': '5270da3a106a6c1631000000',
                'dataset': '5270da3a106a6c1631000000'}
        errors = {
            'aws_instance': u'Instance not found',
            'dataset': 'DataSet not found'}
        _check(data, errors)

        data = {'examples_fields': 'hire_outcome,application_id',
                'examples_placement': app.db.Test.EXAMPLES_TO_MONGO,
                'spot_instance_type': 'INVALID',
                'start': '2013-01-01'}
        errors = {
            'spot_instance_type': "INVALID is invalid choice for \
spot_instance_type. Please choose one of ('m3.xlarge', 'm3.2xlarge', \
'cc2.8xlarge', 'cr1.8xlarge', 'hi1.4xlarge', 'hs1.8xlarge')",
            'parameters': 'Parameters category, end are required',
            None: 'One of parameters, dataset is required.'  # TODO: Remove.
        }
        _check(data, errors)

    def test_delete(self):
        self.check_related_docs_existance(self.db.TestExample)
        self._check_delete()

        self.check_related_docs_existance(self.db.TestExample, exist=False,
                                          msg='Tests Examples should be \
when remove test')

        # Checks whether not all docs was deleted
        self.assertTrue(self.db.Test.find().count(),
                        "All tests was deleted!")
        self.assertTrue(self.db.TestExample.find().count(),
                        "All examples was deleted!")
