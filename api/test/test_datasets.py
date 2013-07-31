import httplib
import json
from bson.objectid import ObjectId
from mock import patch

from utils import BaseTestCase
from api.views import DataSetResource


class DataSetsTests(BaseTestCase):
    """
    Tests of the DataSetsTests API.
    """
    HANDLER_ID = '5170dd3a106a6c1631000000'
    DS_ID = '5270dd3a106a6c1631000000'
    FIXTURES = ('importhandlers.json', 'datasets.json')
    RESOURCE = DataSetResource
    BASE_URL = '/cloudml/importhandlers/%s/datasets/' % HANDLER_ID

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.Model = self.db.DataSet
        self.obj = self.Model.find_one({'_id': ObjectId(self.DS_ID)})

    @patch('api.models.DataSet.save_to_s3')
    def test_post(self, save_to_s3_mock):
        """
        Tests loading dataset using specified import handler
        """
        post_data = {'start': '2012-12-03',
                     'end': '2012-12-04',
                     'category': 'smth'}
        resp, ds = self._check_post(post_data=post_data, load_model=True)
        self.assertEquals(ds.status, 'Imported', ds.error)
        self.assertEquals(ds.import_handler_id, self.HANDLER_ID)
        self.assertEquals(ds.records_count, 99)
        self.assertEquals(ds.import_params, post_data)
        self.assertTrue(ds.compress)
        self.assertTrue(save_to_s3_mock.called)
        self.assertEquals(ds.filename, 'test_data/%s.gz' % ds._id)

    @patch('api.models.DataSet.get_s3_download_url')
    def test_generate_url_action(self, url_mock):
        """
        Tests generation Amazon S3 url method.
        """
        url_mock.return_value = 'example.com'
        url = self._get_url(id=self.obj._id, action='generate_url')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEquals(data['dataset'], self.DS_ID)
        self.assertEquals(data['url'], 'example.com')

    def test_list(self):
        self._check_list(show='name,status')

    def test_details(self):
        self._check_details(show='name,status')

    def test_delete(self):
        import shutil
        filename = self.obj.filename
        shutil.copy2(filename, filename + '.bak')
        self._check_delete()
        shutil.move(filename + '.bak', filename)
