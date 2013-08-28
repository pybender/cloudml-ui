import httplib
import json
from bson.objectid import ObjectId
from mock import patch
from moto import mock_s3

from utils import BaseTestCase, HTTP_HEADERS
from api.views import DataSetResource


class DataSetsTests(BaseTestCase):
    """
    Tests of the DataSetsTests API.
    """
    HANDLER_ID = '5170dd3a106a6c1631000000'
    DS_ID = '5270dd3a106a6c1631000000'
    DS_ID2 = '5270dd3a106a6c1631000111'
    TEST_ID = '000000000000000000000002'
    MODEL_ID = '519318e6106a6c0df349bc0b'
    FIXTURES = ('tests.json', 'models.json', 'importhandlers.json', 'datasets.json')
    RESOURCE = DataSetResource
    BASE_URL = '/cloudml/importhandlers/%s/datasets/' % HANDLER_ID

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.Model = self.db.DataSet
        self.obj = self.Model.find_one({'_id': ObjectId(self.DS_ID)})

    @mock_s3
    def test_post(self):
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
        self.assertIsNotNone(ds.data)
        self.assertTrue(ds.on_s3)
        self.assertEquals(ds.filename, 'test_data/%s.gz' % ds._id)

    @patch('core.importhandler.importhandler.ImportHandler.__init__')
    def test_post_exception(self, mock_handler):
        mock_handler.side_effect = Exception('Some message')

        post_data = {'start': '2012-12-03',
                'end': '2012-12-04',
                'category': 'smth'}
        url = self._get_url()
        resp = self.app.post(url, data=post_data, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, httplib.CREATED)
        data = json.loads(resp.data)

        dataset = self.db.DataSet.get_from_id(ObjectId(data['dataset']['_id']))
        self.assertEqual(dataset.status, dataset.STATUS_ERROR)
        self.assertEqual(dataset.error, 'Some message')

    def test_edit_name(self):
        url = self._get_url(id=self.obj._id)
        data = {'name': 'new name'}
        resp = self.app.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        dataset = self.Model.find_one({'_id': ObjectId(self.DS_ID)})
        self.assertEquals(dataset.name, data['name'])

    @mock_s3
    def test_generate_url_action(self):
        """
        Tests generation Amazon S3 url method.
        """
        url = self._get_url(id=self.obj._id, action='generate_url')
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEquals(data['dataset'], self.DS_ID)
        self.assertTrue(data['url'].startswith('https://'))
        self.assertTrue('s3.amazonaws.com' in data['url'])

    def test_list(self):
        self._check_list(show='name,status')

    def test_details(self):
        self._check_details(show='name,status')

    def test_delete(self):
        test = self.db.Test.get_from_id(ObjectId(self.TEST_ID))
        test.dataset = self.obj
        test.save()

        model = self.db.Model.get_from_id(ObjectId(self.MODEL_ID))
        model.dataset_ids = [ObjectId(ds_id) for ds_id in
                             [self.DS_ID, self.DS_ID2]]
        model.save()

        import shutil
        filename = self.obj.filename
        shutil.copy2(filename, filename + '.bak')
        self._check_delete()
        shutil.move(filename + '.bak', filename)

        test.reload()
        model.reload()

        self.assertIsNone(test.dataset)
        self.assertEquals(model.dataset_ids, [ObjectId(self.DS_ID2)])
