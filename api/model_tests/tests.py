import httplib
import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import TestsResource, TestExamplesResource
from models import TestResult, TestExample
from api.ml_models.fixtures import ModelData
from api.import_handlers.fixtures import ImportHandlerData, DataSetData
from fixtures import TestResultData, TestExampleData


class TestTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Test API.
    """
    BASE_URL = '/cloudml/models/{0!s}/tests/'
    RESOURCE = TestsResource
    Model = TestResult
    datasets = [ImportHandlerData, DataSetData, ModelData, TestResultData]

    def setUp(self):
        super(TestTests, self).setUp()
        self.obj = self.Model.query.filter_by(
            name=TestResultData.test_01.name).one()
        self.BASE_URL = self.BASE_URL.format(self.obj.model.id)
        self.MODEL_PARAMS = {'model_id': self.obj.model.id}
        self.RELATED_PARAMS = {'test_result_id': self.obj.id,
                               'model_id': self.obj.model.id}

    def test_list(self):
        self.check_list(show='', query_params=self.MODEL_PARAMS)
        self.check_list(show='name,status', query_params=self.MODEL_PARAMS)

    def test_details(self):
        self.check_details(show='name,status')

    # TODO: further tests


class TestExamplesTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Test Examples API.
    """
    RESOURCE = TestExamplesResource
    Model = TestExample
    datasets = [ImportHandlerData, DataSetData, ModelData,
                TestResultData, TestExampleData]

    def setUp(self):
        super(TestExamplesTests, self).setUp()
        self.test = TestResult.query.filter_by(
            name=TestResultData.test_01.name).first()
        self.model = self.test.model
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
            open('./api/fixtures/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        mock_get_vect_data.return_value = [0.123, 0.0] * 500

        url = self._get_url(id=self.obj.id)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_trainer.called)
        data = json.loads(resp.data)['data']

        for key in ['css_class', 'model_weight', 'transformed_weight',
                    'value', 'vect_value', 'weight']:
            self.assertTrue(key in data['weighted_data_input']['opening_id'])
