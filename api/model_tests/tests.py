import httplib
import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import TestsResource, TestExamplesResource
from models import Test, TestExample
# from api.ml_models.fixtures import ModelData
# from api.import_handlers.fixtures import DataSetData
from fixtures import TestData


class TestTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Test API.
    """
    BASE_URL = '/cloudml/models/{0!s}/tests/'
    RESOURCE = TestsResource
    TEST_NAME = 'Test-1'
    Model = Test
    datasets = [TestData]

    def setUp(self):
        super(TestTests, self).setUp()
        self.obj = self.Model.query.filter_by(name=self.TEST_NAME).one()
        self.BASE_URL = self.BASE_URL.format(self.obj.model.id)
        self.MODEL_PARAMS = {'model_id': self.obj.model.id}
        self.RELATED_PARAMS = {'test_id': self.obj.id,
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
    datasets = [TestData]

    def setUp(self):
        super(TestExamplesTests, self).setUp()
        self.obj = self.Model.query.get()
        self.BASE_URL = '/cloudml/models/%s/tests/%s/examples/'.format(

        )
