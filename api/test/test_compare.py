import httplib
import json
import urllib

from utils import BaseTestCase, HTTP_HEADERS


class CompareReportTests(BaseTestCase):
    """
    Tests of the CompareReport API.
    """
    BASE_URL = '/cloudml/reports/compare/'
    FIXTURES = ('models.json', 'tests.json', 'examples.json',)
    MODEL1_NAME = 'TrainedModel'
    MODEL2_NAME = 'OtherModel'
    TEST1_NAME = 'Test-1'
    TEST2_NAME = 'Test-3'

    def setUp(self):
        super(CompareReportTests, self).setUp()
        self.model1 = self.db.Model.find_one({'name': self.MODEL1_NAME})
        self.model2 = self.db.Model.find_one({'name': self.MODEL2_NAME})
        self.test1 = self.db.Test.find_one({'name': self.TEST1_NAME})
        self.test1.model_id = str(self.model1._id)
        self.test1.save()
        self.test2 = self.db.Test.find_one({'name': self.TEST2_NAME})
        self.test2.model_id = str(self.model2._id)
        self.test2.save()

    def test_compare(self):
        url = '{0}?{1}'.format(
            self.BASE_URL,
            urllib.urlencode({
                'model1': str(self.model1._id),
                'model2': str(self.model2._id),
                'test1': str(self.test1._id),
                'test2': str(self.test2._id),
            })
        )
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)['data']
        self.assertEquals(len(data), 2)
        self.assertEquals(data[0]['test']['_id'], str(self.test1._id))
        self.assertEquals(data[1]['test']['_id'], str(self.test2._id))
        self.assertTrue('examples' in data[0])
        self.assertTrue('examples' in data[1])
