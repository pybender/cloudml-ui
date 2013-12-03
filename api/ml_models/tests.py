import httplib
import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import ModelResource
from models import Model
from fixtures import ModelData


class ModelsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Model API.
    """
    BASE_URL = '/cloudml/models/'
    RESOURCE = ModelResource
    Model = Model
    datasets = [ModelData]

    def setUp(self):
        super(ModelsTests, self).setUp()
        self.obj = self.Model.query.filter_by(name="TrainedModel").one()

    def test_list(self):
        self.check_list(show='')
        self.check_list(show='created_on,updated_on')

    # def test_filter(self):
    #     self.check_list()
    #     self.check_filter({'status': 'New'})
    #     # No name filter - all models should be returned
    #     self.check_filter({'name': 'Test'}, {})
    #
    #     # Comparable filter
    #     self.check_filter({'comparable': 1}, {'comparable': True})
    #     self.check_filter({'comparable': 0}, {'comparable': False})

    def test_details(self):
        self.check_details(show='')
        self.check_details(show='created_on,labels')
