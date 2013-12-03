import httplib
import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import ImportHandlerResource, DataSetResource
from models import ImportHandler, DataSet
from fixtures import ImportHandlerData, DataSetData
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model


class ImportHandlerTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the ImportHandlers API.
    """
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource
    MODEL_NAME = 'TrainedModel'
    Model = ImportHandler
    datasets = [ModelData, ImportHandlerData, DataSetData]

    def setUp(self):
        super(ImportHandlerTests, self).setUp()
        self.obj = self.Model.query.filter_by(name='Handler 1').one()

    def test_list(self):
        self.check_list(show='name,type,import_params')

    def test_details(self):
        resp = self.check_details(
            show='name,type,import_params,data', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['type'], self.obj.type)
        self.assertEqual(obj['import_params'], self.obj.import_params)
        self.assertEqual(obj['data'], self.obj.data)

    def test_edit_name(self):
        url = self._get_url(id=self.obj.id)
        data = {'name': 'new name'}
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        handler = self.Model.query.get(self.obj.id)
        self.assertEquals(handler.name, data['name'])

    def test_delete(self):
        datasets = DataSet.query.filter_by(import_handler_id=self.obj.id)
        self.assertEquals(datasets.count(), 3, 'Invalid fixtures')
        import shutil
        files = []
        for dataset in datasets.all():
            files.append(dataset.filename)
            shutil.copy2(dataset.filename, dataset.filename + '.bak')

        model = Model.query.filter_by(name=self.MODEL_NAME).one()
        model.test_import_handler_id = self.obj.id
        model.train_import_handler_id = self.obj.id
        model.save()

        url = self._get_url(id=self.obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)

        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertIsNone(self.Model.query.filter_by(name='Handler 1').first())

        datasets = DataSet.query.filter_by(import_handler_id=self.obj.id)
        self.assertFalse(datasets.count(), 'DataSets should be removed')
        for filename in files:
            shutil.move(filename + '.bak', filename)

        model = Model.query.filter_by(name=self.MODEL_NAME).one()
        self.assertIsNone(model.test_import_handler, 'Ref should be removed')
        self.assertIsNone(model.train_import_handler, 'Ref should be removed')

    def test_download(self):
        url = self._get_url(id=self.obj.id, action='download')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(resp.mimetype, 'text/plain')
        self.assertEquals(resp.headers['Content-Disposition'],
                          'attachment; filename=importhandler-%s.json' %
                          self.obj.name)


class DataSetsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the DataSetsTests API.
    """
    HANDLER_ID = 1
    DS_NAME = 'DS'
    DS_NAME2 = 'DS 2'
    RESOURCE = DataSetResource
    BASE_URL = '/cloudml/importhandlers/%s/datasets/' % HANDLER_ID
    Model = DataSet
    datasets = [ModelData, ImportHandlerData, DataSetData]

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.obj = self.Model.query.filter_by(name=self.DS_NAME).one()

    def test_list(self):
        self.check_list(show='name,status,filename,filesize,records_count')

    def test_details(self):
        resp = self.check_details(
            show='name,status,filename,data_fields', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['status'], self.obj.status)
        self.assertEqual(obj['data_fields'], self.obj.data_fields)

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_post(self, mock_multipart_upload):
        """
        Tests loading dataset using specified import handler
        """
        params = {'start': '2012-12-03',
                  'end': '2012-12-04', 'category': 'smth'}
        post_data = {
            'import_params': json.dumps(params),
            'format': DataSet.FORMAT_JSON
        }
        resp, ds = self.check_edit(post_data)
        self.assertEquals(ds.status, 'Imported', ds.error)
        self.assertEquals(ds.import_handler_id, self.HANDLER_ID)
        self.assertEquals(ds.records_count, 99)
        self.assertEquals(ds.import_params, params)
        self.assertTrue(ds.compress)
        self.assertTrue(ds.on_s3)
        self.assertEquals(ds.format, DataSet.FORMAT_JSON)
        self.assertEquals(ds.filename, 'test_data/%s.gz' % ds.id)
        self.assertTrue(mock_multipart_upload.called)
