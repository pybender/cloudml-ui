import json
from bson import ObjectId
from moto import mock_s3
from mock import patch

from utils import BaseTestCase, HTTP_HEADERS
from api.views import TestExamplesResource


class TestExamplesTests(BaseTestCase):
    """
    Tests of the Test Examples API.
    """
    HANDLER_NAME = 'IH1'
    MODEL_NAME = 'TrainedModel'
    TEST_NAME = 'Test-1'
    TEST_NAME2 = 'Test-2'
    DS_ID = '5270dd3a106a6c1631000000'
    FIXTURES = ('datasets.json', 'models.json', 'tests.json', 'examples.json',
                'weights.json')
    RESOURCE = TestExamplesResource

    @mock_s3
    def setUp(self):
        super(TestExamplesTests, self).setUp()
        self.model = self.db.Model.find_one({'name': self.MODEL_NAME})
        self.test = self.db.Test.find_one({'model_name': self.MODEL_NAME,
                                           'name': self.TEST_NAME})
        self.test2 = self.db.Test.find_one({'model_name': self.MODEL_NAME,
                                           'name': self.TEST_NAME2})
        self.dataset = self.db.DataSet.get_from_id(ObjectId(self.DS_ID))

        self.assertIsNotNone(self.dataset)

        model_tests = self.db.Test.find({'model_name': self.MODEL_NAME})
        for test in model_tests:
            test.model_id = str(self.model._id)
            test.dataset = self.dataset
            test.save()

        examples_params = {
            'model_name': self.MODEL_NAME,
            'test_name': {'$in': [self.TEST_NAME, self.TEST_NAME2]}
        }

        for example in self.db.TestExample.find(examples_params):
            example.model_id = str(self.model._id)
            example.test_id = str(self.test._id) \
                if example.test_name == self.TEST_NAME \
                else str(self.test2._id)
            example.data_input = {
                'opening_id': "201913099"
            }
            example.save()

        self.Model = self.db.TestExample
        self.obj = self.db.TestExample.find_one({'test_id': str(self.test._id)})
        self.obj.vect_data = [0.123, 0.0] * 217
        self.obj.data_input = {
            'opening_id': "201913099"
        }
        self.obj.save()

        self.BASE_URL = '/cloudml/models/%s/tests/%s/examples/' % \
            (self.model._id, self.test._id)

    @mock_s3
    @patch('api.models.DataSet.get_data_stream')
    def test_list(self, mock_get_data_stream):
        self._check_list(show='created_on,label,pred_label', query_params={
            'test_id': str(self.test._id)
        })
        self.assertFalse(mock_get_data_stream.called)

        # Data filter, not stored at s3
        url = '{0}?{1}&{2}'.format(
            self.BASE_URL,
            'action=examples:list',
            'data_input.employer->country=United Kingdom'
        )
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertFalse(mock_get_data_stream.called)

        # Data filter, when stored at s3
        url = '/cloudml/models/{0!s}/tests/{1!s}/examples/?{2}&{3}'.format(
            self.model._id,
            self.test2._id,
            'action=examples:list',
            'data_input.employer->country=United Kingdom'
        )
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_data_stream.called)

    @mock_s3
    def test_details(self):
        self._check_details(show='id,test_name')

    @mock_s3
    @patch('api.models.Model.get_trainer')
    def test_details_weight(self, mock_get_trainer):
        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(
            open('./api/fixtures/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        url = self._get_url(id=self.obj._id,
                            show='id,test_name,weighted_data_input')
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_trainer.called)
        data = json.loads(resp.data)['data']

        for key in ['css_class', 'model_weight', 'transformed_weight',
                    'value', 'vect_value', 'weight']:
            self.assertTrue(key in data['weighted_data_input']['opening_id'])

    def test_groupped(self):
        url = self._get_url(action='groupped',
                            field='data_input.opening_id', count='2')
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEquals(data['field_name'], 'data_input.opening_id')
        item = data['datas']['items'][0]
        self.assertEquals(item['count'], 3)
        self.assertEquals(item['group_by_field'], '201913099')
        self.assertTrue(item['avp'] > 0)
        self.assertTrue(data['mavp'] > 0)

    def test_datafields(self):
        url = self._get_url(action='datafields')
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEquals(data['fields'], ['employer->country'])

    @patch('api.tasks.get_csv_results')
    def test_csv(self, mock_get_csv):
        fields = 'name,id,label,pred_label,prob,data_input.employer->country'
        url = self._get_url(action='csv', show=fields)
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_csv.delay.called)
