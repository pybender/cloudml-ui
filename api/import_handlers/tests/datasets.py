import httplib
import json
import os
from datetime import datetime

from mock import patch, MagicMock

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..views import DataSetResource
from ..models import DataSet, XmlImportHandler as ImportHandler
from ..fixtures import DataSetData, IMPORT_HANDLER_FIXTURES, \
    XmlImportHandlerData as ImportHandlerData
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.model_tests.fixtures import TestResultData
from api.model_tests.models import TestResult
from api.features.fixtures import FeatureSetData, FeatureData
from api.servers.models import Server
from api.servers.fixtures import ServerData


class DataSetsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the DataSets API.
    """
    DS_NAME = DataSetData.dataset_01.name
    DS_NAME2 = DataSetData.dataset_02.name
    MODEL_NAME = ModelData.model_01.name
    RESOURCE = DataSetResource
    Model = DataSet
    datasets = [FeatureData, FeatureSetData, DataSetData,
                ModelData, TestResultData] + IMPORT_HANDLER_FIXTURES

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        for ds in DataSet.query.all():
            ds.import_handler_id = self.handler.id
            ds.import_handler_type = self.handler.TYPE
            ds.import_handler_xml = self.handler.data
            ds.save()
        self.obj = DataSet.query.filter_by(
            import_handler_id=self.handler.id, name=self.DS_NAME).first()
        self.assertTrue(self.obj)
        self.BASE_URL = '/cloudml/importhandlers/xml/%s/datasets/' \
            % self.handler.id

    def test_list(self):
        self.check_list(show='name,status,filename,filesize,records_count')

    def test_details(self):
        resp = self.check_details(
            show='name,status,filename,data_fields', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['status'], self.obj.status)
        self.assertEqual(obj['data_fields'], self.obj.data_fields)

    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    def test_post(self, mock_load_key, mock_multipart_upload):
        params = {'start': '2012-12-03',
                  'end': '2012-12-04'}
        post_data = {
            'import_params': json.dumps(params),
            'format': DataSet.FORMAT_JSON
        }
        resp, ds = self.check_edit(post_data, )
        self.assertEquals(ds.status, 'Imported', ds.error)
        self.assertEquals(ds.import_handler_id, self.handler.id)
        self.assertEquals(ds.records_count, 100)
        self.assertEquals(ds.import_params, params)
        self.assertTrue(ds.compress)
        self.assertTrue(ds.on_s3)
        self.assertTrue(ds.uid)
        self.assertEquals(ds.format, DataSet.FORMAT_JSON)
        self.assertEquals(ds.filename, 'test_data/%s.gz' % ds.uid)
        self.assertTrue(mock_multipart_upload.called)

        # Check created dataset
        stream = ds.get_data_stream()
        self.assertTrue(stream)
        self.assertFalse(mock_load_key.called)

        os.remove(ds.filename)
        stream = ds.get_data_stream()
        self.assertTrue(stream)
        self.assertTrue(mock_load_key.called)

    @patch('cloudml.importhandler.importhandler.ImportHandler.__init__')
    def test_post_exception(self, mock_handler):
        mock_handler.side_effect = Exception('Some message')

        params = {'start': '2012-12-03',
                  'end': '2012-12-04', 'category': 'smth'}
        post_data = {
            'import_params': json.dumps(params),
            'format': DataSet.FORMAT_JSON
        }
        url = self._get_url(id=self.obj.import_handler.id)
        resp = self.client.post(url, data=post_data, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, httplib.CREATED)
        data = json.loads(resp.data)

        dataset = DataSet.query.get(data[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(dataset.status, dataset.STATUS_ERROR)
        self.assertEqual(dataset.error, 'Some message')

    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_post_csv(self, mock_multipart_upload):
        params = {'start': '2012-12-03',
                  'end': '2012-12-04'}
        post_data = {
            'import_params': json.dumps(params),
            'format': DataSet.FORMAT_CSV
        }
        resp, ds = self.check_edit(post_data)
        self.assertEquals(ds.status, 'Imported', ds.error)
        self.assertEquals(ds.import_handler_id, self.handler.id)
        self.assertEquals(ds.import_handler_xml, self.handler.data)
        self.assertEquals(ds.records_count, 100)
        self.assertEquals(ds.import_params, params)
        self.assertTrue(ds.compress)
        self.assertTrue(ds.on_s3)
        self.assertEquals(ds.format, DataSet.FORMAT_CSV)
        self.assertEquals(ds.filename, 'test_data/%s.gz' % ds.uid)
        self.assertTrue(mock_multipart_upload.called)

    def test_edit_name(self):
        url = self._get_url(id=self.obj.id)
        data = {'name': 'new name'}
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        dataset = self.Model.query.get(self.obj.id)
        self.assertEquals(dataset.name, data['name'])

    def test_edit_locked(self):
        # test locked dataset
        self.obj.locked = True
        self.obj.save()
        data = {'name': 'new name1'}
        url = self._get_url(id=self.obj.id)
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('Some existing models were trained/tested', resp.data)

    @patch('api.amazon_utils.AmazonS3Helper.get_download_url')
    def test_generate_url_action(self, dl_mock):
        """
        Tests generation Amazon S3 url method.
        """
        dl_mock.return_value = 'https://s3.amazonaws.com/url'
        url = self._get_url(id=self.obj.id, action='generate_url')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME], self.obj.id)
        self.assertTrue(data['url'].startswith('https://'))
        self.assertTrue('s3.amazonaws.com' in data['url'])

    def test_pig_fields(self):
        ds = DataSet.query.filter_by(name='DS (pig)').one()
        resp = self._check(action='pig_fields', id=ds.id)
        self.assertItemsEqual(
            ['metric', 'opening', 'title'],
            [fld['column_name'] for fld in resp['fields']]
        )
        self.assertTrue(
            '<field name="metric" type="float" />' in resp['sample_xml'],
            resp['sample_xml'])

    @patch('api.import_handlers.tasks.upload_dataset')
    def test_reupload_action(self, mock_upload_dataset):
        """
        Tests reupload to Amazon S3.
        """
        url = self._get_url(id=self.obj.id, action='reupload')

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertFalse(mock_upload_dataset.delay.called)

        self.obj.status = self.obj.STATUS_ERROR
        self.obj.save()

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['id'], self.obj.id)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['status'],
                          DataSet.STATUS_IMPORTING)
        mock_upload_dataset.delay.assert_called_once_with(self.obj.id)

    @patch('api.import_handlers.tasks.import_data')
    def test_reimport_action(self, mock_import_data):
        """
        Tests re-import.
        """
        url = self._get_url(id=self.obj.id, action='reimport')

        self.obj.status = self.obj.STATUS_IMPORTED
        self.obj.save()

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['id'],
                          self.obj.id)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['status'],
                          DataSet.STATUS_IMPORTING)
        mock_import_data.delay.assert_called_once_with(dataset_id=self.obj.id)
        mock_import_data.reset_mock()

        self.obj.status = DataSet.STATUS_IMPORTING
        self.obj.save()

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertFalse(mock_import_data.delay.called)

        # test locked dataset
        self.obj.locked = True
        self.obj.save()
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('Data set is locked for modifications', resp.data)

    @patch('api.logs.models.LogMessage')
    def test_delete(self, *mocks):
        test = TestResult.query.filter_by(name='Test-1').first()
        test.dataset = self.obj
        test.save()

        model = Model.query.filter_by(name=self.MODEL_NAME).first()
        model.datasets.append(self.obj)
        model.datasets.append(DataSet.query.filter_by(name='DS 2').first())
        model.save()
        self.assertEquals([ds.name for ds in model.datasets], ['DS', 'DS 2'])

        import shutil
        filename = self.obj.filename
        shutil.copy2(filename, filename + '.bak')
        self.check_delete(self.obj)
        shutil.move(filename + '.bak', filename)

        model = Model.query.filter_by(name=self.MODEL_NAME).first()
        test = TestResult.query.filter_by(name='Test-1').first()

        self.assertIsNone(test.dataset)
        self.assertEquals([ds.name for ds in model.datasets], ['DS 2'])

    def test_sample_data_action(self):
        # 1. getting sample of default size 10
        url = self._get_url(id=self.obj.id, action='sample_data')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEqual(10, len(data))
        self.assertNotEqual(data[0], data[-1])
        self.assertNotEqual(data[1], data[-2])

        # 2. test getting sample of size 5
        url = self._get_url(id=self.obj.id, action='sample_data', size=5)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEqual(5, len(data))

        # 3. dataset not found
        url = self._get_url(id=1010, action='sample_data')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)

        # 4. file not found
        with patch('os.path.exists') as path_exists_mock:
            path_exists_mock.return_value = False
            url = self._get_url(id=self.obj.id, action='sample_data')
            resp = self.client.get(url, headers=HTTP_HEADERS)
            self.assertEquals(resp.status_code, httplib.NOT_FOUND)

        # 5. unknown file type
        with patch('os.path.splitext') as path_splitext_mock:
            path_splitext_mock.return_value = ('filename', '.zip')
            url = self._get_url(id=self.obj.id, action='sample_data')
            resp = self.client.get(url, headers=HTTP_HEADERS)
            self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
            self.assertTrue('unknown file type' in resp.data)

    def test_unlock(self):
        data_set = DataSet.query.filter_by(
            name=DataSetData.dataset_01.name).one()
        data_set.locked = True
        data_set.save()
        data_set.unlock()
        # this should not be unlocked
        self.assertTrue(data_set.locked)

        data_set = DataSet.query.filter_by(
            name=DataSetData.dataset_04.name).one()
        data_set.locked = True
        data_set.save()
        data_set.unlock()
        # this should be unlocked
        self.assertFalse(data_set.locked)


class TestTasksTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the celery tasks.
    """
    datasets = [DataSetData, ModelData, TestResultData] + \
        IMPORT_HANDLER_FIXTURES

    @patch('api.logs.models.LogMessage')
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_upload_dataset(self, mock_multipart_upload, *mocks):
        from api.import_handlers.tasks import upload_dataset
        dataset = DataSet.query.filter_by(
            name=DataSetData.dataset_01.name).one()
        upload_dataset(dataset.id)
        mock_multipart_upload.assert_called_once_with(
            str(dataset.uid),
            dataset.filename,
            {
                'params': str(dataset.import_params),
                'handler': dataset.import_handler_id,
                'dataset': dataset.name
            }
        )
        self.assertEquals(dataset.status, dataset.STATUS_IMPORTED)
