from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from api.ml_models.fixtures import ModelData
from api.features.fixtures import FeatureSetData, FeatureData
from views import StatisticsResource


class StatisticsTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the Statistics API. """
    datasets = [FeatureData, FeatureSetData,
                ModelData]  # TODO: TestData, DataSetData
    BASE_URL = '/cloudml/statistics/'
    RESOURCE = StatisticsResource

    def test_get(self):
        resp = self._check()
        data = resp['statistics']
        self.assertTrue('models' in data)
        self.assertTrue('datasets' in data)
        self.assertTrue('tests' in data)
