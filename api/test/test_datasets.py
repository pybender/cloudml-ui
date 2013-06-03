from utils import BaseTestCase
from api.views import DataSetResource


class DataSetsTests(BaseTestCase):
    """
    Tests of the DataSetsTests API.
    """
    HANDLER_ID = '5170dd3a106a6c1631000000'
    DS_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('importhandlers.json', 'datasets.json' )
    RESOURCE = DataSetResource

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.BASE_URL = '/cloudml/importhandlers/%s/datasets/' % self.HANDLER_ID
        self.Model = self.db.DataSet
        self.obj = self.Model.find_one({'_id': self.DS_ID})

    # def test_list(self):
    #     self._check_list()
