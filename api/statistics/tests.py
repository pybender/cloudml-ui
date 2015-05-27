# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from api.ml_models.fixtures import ModelData, MODELS_COUNT
from api.ml_models.models import Model
from api.features.fixtures import FeatureSetData, FeatureData
from api.model_tests.fixtures import TestResultData
from api.import_handlers.fixtures import DataSetData
from views import StatisticsResource


class StatisticsTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the Statistics API. """
    datasets = [FeatureData, FeatureSetData,
                ModelData, TestResultData, DataSetData]
    BASE_URL = '/cloudml/statistics/'
    RESOURCE = StatisticsResource

    def test_get(self):
        resp = self._check()
        data = resp['statistics']

        self.assertTrue('models' in data)
        self.assertTrue(data['models']['count'], MODELS_COUNT)
        model_data = data['models']['data']
        for status in Model.STATUSES:
            count = Model.query.filter_by(status=status).count()
            if count:
                self.assertTrue(model_data[status], count)

        self.assertTrue('datasets' in data)
        self.assertTrue('tests' in data)
