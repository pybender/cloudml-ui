import json
from mock import patch, MagicMock
from bson.objectid import ObjectId
from moto import mock_s3

from utils import BaseTestCase, HTTP_HEADERS
from utils import MODEL_ID
from api.views import Tests as TestResource


class TestTests(BaseTestCase):
    TEST_ID = '000000000000000000000002'
    DS_ID = '5270dd3a106a6c1631000000'
    MODEL_PARAMS = {'model_id': MODEL_ID}
    RELATED_PARAMS = {'test_id': TEST_ID, 'model_id': MODEL_ID}
    RESOURCE = TestResource
    FIXTURES = ('datasets.json', 'importhandlers.json', 'models.json',
                'tests.json', 'examples.json', 'instances.json', )

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
        data = {'start': '2012-12-03',
                'end': '2012-12-04',
                'category': 'smth',
                'aws_instance': '5170dd3a106a6c1631000000'}
        resp, test = self._check_post(data, load_model=True)
        data = json.loads(resp.data)

        self.assertEquals(test.status, test.STATUS_IMPORTED)
        self.assertTrue(mock_run_test.subtask.called)
        self.assertTrue('test' in data)

    @mock_s3
    @patch('api.tasks.run_test')
    def test_post_with_dataset(self, mock_run_test):
        data = {'dataset': self.DS_ID,
                'aws_instance': '5170dd3a106a6c1631000000'}
        resp = self.app.post(self._get_url(), data=data, headers=HTTP_HEADERS)
        data = json.loads(resp.data)
        self.assertEquals(resp.status_code, 201)

        test = self.db.Test.get_from_id(ObjectId(data['test']['_id']))

        self.assertEquals(test.status, test.STATUS_QUEUED)
        self.assertTrue(mock_run_test.apply_async.called)
        self.assertTrue('test' in data)

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
