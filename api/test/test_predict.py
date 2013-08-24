from bson import ObjectId

from utils import BaseTestCase, HTTP_HEADERS
from api.views import Predict


class PredictTests(BaseTestCase):
    """
    Tests of the Predict API.
    """
    BASE_URL = '/cloudml/model/'
    MODEL_NAME = 'TrainedModel'
    HANDLER_ID = '5170dd3a106a6c1631000000'

    FIXTURES = ('importhandlers.json', 'models.json',
                'tests.json', 'examples.json', 'datasets.json',)

    def setUp(self):
        super(PredictTests, self).setUp()
        self.model = self.db.Model.find_one({'name': self.MODEL_NAME})
        self.handler = self.db.ImportHandler.find_one({'_id': ObjectId(self.HANDLER_ID)})

    def test_predict(self):
        url = '{0}{1!s}/{2!s}/predict'.format(
            self.BASE_URL,
            self.model._id,
            self.handler._id,
        )
        # TODO: fix that view
        # resp = self.app.post(url, headers=HTTP_HEADERS)
        # self.assertEquals(resp.status_code, httplib.OK)
