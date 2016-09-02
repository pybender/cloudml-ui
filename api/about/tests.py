# Authors: Anna Lysak <annalysak@cloud.upwork.com>

from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from views import AboutResource


class AboutTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the Statistics API. """
    datasets = []
    BASE_URL = '/cloudml/about/'
    RESOURCE = AboutResource

    def test_get(self):
        resp = self._check()
        data = resp['about']
        self.assertTrue('version' in data)
        self.assertTrue('releasenotes' in data)
