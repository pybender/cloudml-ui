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
from api.model_tests.fixtures import TestResultData
from api.model_tests.models import TestResult


class ImportHandlerTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the ImportHandlers API.
    """
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource
    MODEL_NAME = 'TrainedModel'
    Model = ImportHandler
    datasets = [ImportHandlerData, DataSetData, ModelData]

    def setUp(self):
        super(ImportHandlerTests, self).setUp()
        self.obj = self.Model.query.filter_by(name='Handler 1').first()
        for ds in DataSet.query.all():
            ds.import_handler = self.obj
            ds.save()

    def test_list(self):
        self.check_list(show='name,type,import_params')

    def test_details(self):
        resp = self.check_details(
            show='name,type,import_params,data', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['type'], self.obj.type)
        self.assertEqual(obj['import_params'], self.obj.import_params)
        self.assertEqual(
            obj['data']['target-schema'],
            self.obj.data['target-schema']
        )

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

        model = Model.query.filter_by(name=self.MODEL_NAME).first()
        model.test_import_handler_id = self.obj.id
        model.train_import_handler_id = self.obj.id
        model.save()

        url = self._get_url(id=self.obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)

        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertIsNone(self.Model.query.filter_by(id=self.obj.id).first())

        datasets = DataSet.query.filter_by(import_handler_id=self.obj.id)
        self.assertFalse(datasets.count(), 'DataSets should be removed')
        for filename in files:
            shutil.move(filename + '.bak', filename)

        model = Model.query.filter_by(name=self.MODEL_NAME).first()
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
    DS_NAME = 'DS'
    DS_NAME2 = 'DS 2'
    MODEL_NAME = 'TrainedModel'
    RESOURCE = DataSetResource
    Model = DataSet
    datasets = [ImportHandlerData, DataSetData, ModelData, TestResultData]

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.handler = ImportHandler.query.filter_by(name='Handler 1').first()
        self.obj = self.Model.query.filter_by(name=self.DS_NAME).first()
        self.BASE_URL = '/cloudml/importhandlers/%s/datasets/' % self.obj.id
        for ds in DataSet.query.all():
            ds.import_handler = self.handler
            ds.save()

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
        self.assertEquals(ds.import_handler_id, self.handler.id)
        self.assertEquals(ds.records_count, 99)
        self.assertEquals(ds.import_params, params)
        self.assertTrue(ds.compress)
        self.assertTrue(ds.on_s3)
        self.assertEquals(ds.format, DataSet.FORMAT_JSON)
        # TODO
        # self.assertEquals(ds.filename, 'test_data/%s.gz' % ds.id)
        self.assertTrue(mock_multipart_upload.called)

    @patch('core.importhandler.importhandler.ImportHandler.__init__')
    def test_post_exception(self, mock_handler):
        mock_handler.side_effect = Exception('Some message')

        params = {'start': '2012-12-03',
                  'end': '2012-12-04', 'category': 'smth'}
        post_data = {
            'import_params': json.dumps(params),
            'format': DataSet.FORMAT_JSON
        }
        url = self._get_url()
        resp = self.client.post(url, data=post_data, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, httplib.CREATED)
        data = json.loads(resp.data)

        dataset = DataSet.query.get(data[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(dataset.status, dataset.STATUS_ERROR)
        self.assertEqual(dataset.error, 'Some message')

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_post_csv(self, mock_multipart_upload):
        """
        Tests loading dataset using specified import handler
        """
        params = {'start': '2012-12-03',
                  'end': '2012-12-04', 'category': 'smth'}
        post_data = {
            'import_params': json.dumps(params),
            'format': DataSet.FORMAT_CSV
        }
        resp, ds = self.check_edit(post_data)
        self.assertEquals(ds.status, 'Imported', ds.error)
        self.assertEquals(ds.import_handler_id, self.handler.id)
        self.assertEquals(ds.records_count, 99)
        self.assertEquals(ds.import_params, params)
        self.assertTrue(ds.compress)
        self.assertTrue(ds.on_s3)
        self.assertEquals(ds.format, DataSet.FORMAT_CSV)
        # TODO
        # self.assertEquals(ds.filename, 'test_data/%s.gz' % ds.id)
        self.assertTrue(mock_multipart_upload.called)

    def test_edit_name(self):
        url = self._get_url(id=self.obj.id)
        data = {'name': 'new name'}
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        dataset = self.Model.query.get(self.obj.id)
        self.assertEquals(dataset.name, data['name'])

    @mock_s3
    def test_generate_url_action(self):
        """
        Tests generation Amazon S3 url method.
        """
        url = self._get_url(id=self.obj.id, action='generate_url')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME], self.obj.id)
        self.assertTrue(data['url'].startswith('https://'))
        self.assertTrue('s3.amazonaws.com' in data['url'])

    @mock_s3
    @patch('api.tasks.upload_dataset')
    def test_reupload_action(self, mock_upload_dataset):
        """
        Tests reupload to Amazon S3.
        """
        url = self._get_url(id=self.obj.id, action='reupload')

        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertFalse(mock_upload_dataset.delay.called)

        # TODO: AttributeError: 'DataSet' object has no attribute '_sa_instance_state'
        # self.obj.status = self.obj.STATUS_ERROR
        # self.obj.save()
        #
        # resp = self.client.put(url, headers=HTTP_HEADERS)
        # self.assertEquals(resp.status_code, httplib.OK)
        # data = json.loads(resp.data)
        # self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['id'], self.obj.id)
        # self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['status'],
        #                   DataSet.STATUS_IMPORTING)
        # mock_upload_dataset.delay.assert_called_once_with(self.obj.id)

    @mock_s3
    @patch('api.tasks.import_data')
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
                          str(self.obj.id))
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['status'],
                          DataSet.STATUS_IMPORTING)
        mock_import_data.delay.assert_called_once_with(dataset_id=self.obj.id)
        mock_import_data.reset_mock()

        # TODO: AttributeError: 'DataSet' object has no attribute '_sa_instance_state'
        # self.obj.status = DataSet.STATUS_IMPORTING
        # self.obj.save()

        # resp = self.client.put(url, headers=HTTP_HEADERS)
        # self.assertEquals(resp.status_code, httplib.OK)
        # self.assertFalse(mock_import_data.delay.called)

    def test_list(self):
        self.check_list(show='name,status')

    def test_details(self):
        self.check_details(obj=self.obj, show='name,status')

    def test_delete(self):
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
