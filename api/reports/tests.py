# Authors: Nikolay Melnik <nmelnik@upwork.com>

import httplib
import json
import urllib

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import CompareReportResource
from api.ml_models.models import Model
from api.ml_models.fixtures import ModelData
from api.model_tests.models import TestResult
from api.model_tests.fixtures import TestResultData, TestExampleData
from api.features.fixtures import FeatureSetData, FeatureData


class CompareReportTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the CompareReport API.
    """
    BASE_URL = '/cloudml/reports/compare/'
    RESOURCE = CompareReportResource
    datasets = [FeatureData, FeatureSetData, ModelData,
                TestResultData, TestExampleData]

    def setUp(self):
        super(CompareReportTests, self).setUp()
        self.model1 = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.model2 = Model.query.filter_by(name=ModelData.model_03.name).one()
        self.test1 = TestResult.query.filter_by(
            name=TestResultData.test_01.name).one()
        self.test2 = TestResult.query.filter_by(
            name=TestResultData.test_05.name).one()

    def test_compare(self):
        url = '{0}?{1}'.format(
            self.BASE_URL,
            urllib.urlencode({
                'model1': self.model1.id,
                'model2': self.model2.id,
                'test1': self.test1.id,
                'test2': self.test2.id,
            })
        )
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)['data']
        self.assertEquals(len(data), 2)
        self.assertEquals(data[0]['test']['id'], self.test1.id)
        self.assertEquals(data[1]['test']['id'], self.test2.id)
        self.assertTrue('examples' in data[0])
        self.assertTrue('examples' in data[1])
