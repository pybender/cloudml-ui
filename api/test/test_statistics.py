import json

from utils import BaseTestCase, HTTP_HEADERS
from api.views import StatisticsResource


class StatisticsTests(BaseTestCase):
    """
    Tests of the Statistics API.
    """
    FIXTURES = ('datasets.json', 'models.json', 'tests.json', 'examples.json')
    BASE_URL = '/cloudml/statistics/'
    RESOURCE = StatisticsResource

    def test_get(self):
        resp = self.app.get(self.BASE_URL, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)['statistics']
        self.assertTrue('models' in data)
        self.assertTrue('datasets' in data)
        self.assertTrue('tests' in data)
