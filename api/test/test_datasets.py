import httplib
import json
from bson.objectid import ObjectId

from api import app
from utils import BaseTestCase
from api.views import DataSetResource


class DataSetsTests(BaseTestCase):
    """
    Tests of the DataSetsTests API.
    """
    HANDLER_ID = '5170dd3a106a6c1631000000'
    DS_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('importhandlers.json', 'datasets.json')
    RESOURCE = DataSetResource

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.BASE_URL = '/cloudml/importhandlers/%s/datasets/' % self.HANDLER_ID
        self.Model = self.db.DataSet
        self.obj = self.Model.find_one({'_id': ObjectId(self.DS_ID)})

    def test_post(self):
        """
        Tests loading dataset using specified import handler
        """
        url = self._get_url()
        data = {'start': '2012-12-03',
                'end': '2012-12-04',
                'category': 'smth'}
        resp = self.app.post(url, data=data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        data = json.loads(resp.data)
        ds_id = data[self.RESOURCE.OBJECT_NAME]['_id']
        ds = app.db.DataSet.find_one({'_id': ObjectId(ds_id)})
        self.assertEquals(ds.status, 'Imported')

    def test_generate_url_action(self):
        """
        Tests generation Amazon S3 url method.
        """
        pass

    # def test_list(self):
    #     self._check_list()
