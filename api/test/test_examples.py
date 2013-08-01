import httplib
from moto import mock_s3

from utils import BaseTestCase


class TestExamplesTests(BaseTestCase):
    """
    Tests of the Test Examples API.
    """
    HANDLER_NAME = 'IH1'
    MODEL_NAME = 'TrainedModel'
    TEST_NAME = 'Test-1'
    FIXTURES = ('models.json', 'tests.json', 'examples.json')

    @mock_s3
    def setUp(self):
        super(TestExamplesTests, self).setUp()
        self.model = self.db.Model.find_one({'name': self.MODEL_NAME})
        self.test = self.db.Test.find_one({'model_name': self.MODEL_NAME,
                                           'name': self.TEST_NAME})
        model_tests = self.db.Test.find({'model_name': self.MODEL_NAME})
        for test in model_tests:
            test.model_id = str(self.model._id)
            test.save()
        for example in self.db.Examples.find({'model_name': self.MODEL_NAME,
                                              'test_name': self.TEST_NAME}):
            example.model_id = str(self.model._id)
            example.test_id = str(self.test._id)
            example.save()

        self.BASE_URL = '/cloudml/models/%s/tests/%s/examples/' % \
            (self.model._id, self.test._id)

    @mock_s3
    def test_list(self):
        # self._check_list()
        pass

    @mock_s3
    def test_details(self):
        # self._check_details()
        pass
