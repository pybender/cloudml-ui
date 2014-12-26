import httplib
import json
import os
from datetime import datetime

from mock import patch, MagicMock
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..views import ImportHandlerResource, DataSetResource
from ..models import ImportHandler, DataSet
from ..fixtures import ImportHandlerData, DataSetData
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.model_tests.fixtures import TestResultData
from api.model_tests.models import TestResult
from api.features.fixtures import FeatureSetData, FeatureData
from api.servers.models import Server
from api.servers.fixtures import ServerData


class ImportHandlerTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the ImportHandlers API.
    """
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource
    MODEL_NAME = ModelData.model_01.name
    Model = ImportHandler
    datasets = [ImportHandlerData, DataSetData, ModelData, ServerData]

    def setUp(self):
        super(ImportHandlerTests, self).setUp()
        self.obj = self.Model.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        # for ds in DataSet.query.all():
        #     ds.import_handler = self.obj
        #     ds.save()

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        resp = self.check_details(
            show='name,type,import_params,data', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['import_params'], self.obj.import_params)
        self.assertEqual(
            obj['data']['target_schema'],
            self.obj.data['target_schema']
        )

    def test_edit_name(self):
        # TODO:
        # data = {'name': ''}
        # self.check_edit_error(data, errors={'fill name': 1}, id=self.obj.id)

        data = {"name": "new name"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.name, data['name'])

    def test_edit_target_schema(self):
        data = {"target_schema": "new-schema"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.data['target_schema'], data['target_schema'])

    def test_edit_datasource(self):
        data = {
            "datasource.0.name": "name2",
            "datasource.0.type": "sql",
            "datasource.0.db": '{"conn": "conn.st", "vendor": "postgres"}'
        }
        resp, obj = self.check_edit(data, id=self.obj.id)
        ds = obj.data['datasource'][0]
        self.assertEquals(ds['name'], "name2")

    def test_edit_queries(self):
        data = {'queries.-1.name': 'new query',
                'queries.-1.sql': 'select * from ...'}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(len(obj.data['queries']), 2, "Query should be added")
        query = obj.data['queries'][1]
        self.assertEquals(query['name'], 'new query')
        self.assertEquals(query['sql'], 'select * from ...')

        data = {'queries.1.name': 'new query1',
                'queries.1.sql': 'select * from t1...'}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(len(obj.data['queries']), 2, "Query should be updated")
        query = obj.data['queries'][1]
        self.assertEquals(query['name'], 'new query1')
        self.assertEquals(query['sql'], 'select * from t1...')

        data = {'queries.1.items.-1.source': 'some-source'}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(len(obj.data['queries'][1]['items']), 1,
                          "Item should be updated")
        item = obj.data['queries'][1]['items'][0]
        self.assertEquals(item['source'], 'some-source')

        data = {'queries.1.items.0.source': 'other-source'}
        resp, obj = self.check_edit(data, id=self.obj.id)
        item = obj.data['queries'][1]['items'][0]
        self.assertEquals(item['source'], 'other-source')

        data = {'queries.1.items.0.target_features.-1.name': 'hire_outcome'}
        resp, obj = self.check_edit(data, id=self.obj.id)
        features = obj.data['queries'][1]['items'][0]['target_features']
        self.assertEquals(len(features), 1,
                          "Item should be updated")
        feature = features[0]
        self.assertEquals(feature['name'], 'hire_outcome')

        data = {'queries.1.items.0.target_features.0.name': 'hire_outcome2'}
        resp, obj = self.check_edit(data, id=self.obj.id)
        feature = obj.data['queries'][1]['items'][0]['target_features'][0]
        self.assertEquals(feature['name'], 'hire_outcome2')

    @patch('api.amazon_utils.AmazonDynamoDBHelper')
    def test_delete(self, mock_aws):
        datasets = DataSet.query.filter_by(import_handler_id=self.obj.id)
        self.assertEquals(datasets.count(), 4, 'Invalid fixtures')
        import shutil
        files = []
        for dataset in datasets.all():
            files.append(dataset.filename)
            shutil.copy2(dataset.filename, dataset.filename + '.bak')

        model = Model.query.filter_by(name=self.MODEL_NAME).first()
        model.test_import_handler = self.obj
        model.train_import_handler = self.obj
        model.save()
        model_id = model.id

        url = self._get_url(id=self.obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)

        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertIsNone(self.Model.query.filter_by(id=self.obj.id).first())

        datasets = DataSet.query.filter_by(import_handler_id=self.obj.id)
        self.assertFalse(datasets.count(), 'DataSets should be removed')
        for filename in files:
            shutil.move(filename + '.bak', filename)

        model = Model.query.get(model_id)
        self.assertTrue(model)
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

    @mock_s3
    @patch('api.servers.tasks.upload_import_handler_to_server')
    def test_upload_to_server(self, mock_task):
        url = self._get_url(id=self.obj.id, action='upload_to_server')
        server = Server.query.filter_by(name=ServerData.server_01.name).one()

        resp = self.client.put(url, data={'server': server.id},
                               headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(mock_task.delay.called)
        self.assertTrue('status' in json.loads(resp.data))

    def test_run_sql_action(self):
        url = self._get_url(id=self.obj.id, action='run_sql')

        # forms validation error
        resp = self.client.put(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue(resp_obj.has_key('response'))
        self.assertTrue(resp_obj['response'].has_key('error'))

        # no parameters
        resp = self.client.put(url,
                               data={'sql': 'SELECT NOW() WHERE %(something)s',
                                     'limit': 2,
                                     'datasource': 'odw'},
                               headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue(resp_obj.has_key('response'))
        self.assertTrue(resp_obj['response'].has_key('error'))

        # good
        iter_mock = MagicMock()
        iter_mock.return_value = [{'now': datetime(2014, 7, 21, 15, 52, 5, 308936)}]
        with patch.dict('api.import_handlers.models.import_handlers.CoreImportHandler.DB_ITERS', {'postgres': iter_mock}):
            resp = self.client.put(url,
                                   data={'sql': 'SELECT NOW() WHERE %(something)s',
                                         'limit': 2,
                                         'datasource': 'odw',
                                         'params': json.dumps({'something': 'TRUE'})},
                                   headers=HTTP_HEADERS)
            resp_obj = json.loads(resp.data)
            self.assertTrue(resp_obj.has_key('data'))
            self.assertTrue(resp_obj['data'][0].has_key('now'))
            self.assertTrue(resp_obj.has_key('sql'))
            iter_mock.assert_called_with(['SELECT NOW() WHERE TRUE LIMIT 2'],
                                         "host='localhost' dbname='cloudml' "
                                         "user='cloudml' password='cloudml'")


class DataSetsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the DataSetsTests API.
    """
    DS_NAME = 'DS'
    DS_NAME2 = 'DS 2'
    MODEL_NAME = ModelData.model_01.name
    RESOURCE = DataSetResource
    Model = DataSet
    datasets = [FeatureData, FeatureSetData, ImportHandlerData, DataSetData,
                ModelData, TestResultData]

    def setUp(self):
        super(DataSetsTests, self).setUp()
        self.handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).first()
        self.obj = self.Model.query.filter_by(name=self.DS_NAME).first()
        self.BASE_URL = '/cloudml/importhandlers/%s/%s/datasets/' \
            % (self.handler.TYPE, self.handler.id)
        for ds in DataSet.query.all():
            ds.import_handler_id = self.handler.id
            ds.import_handler_type = self.handler.TYPE
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
    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    def test_post(self, mock_load_key, mock_multipart_upload):
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

    def test_pig_fields(self):
        ds = DataSet.query.filter_by(name='DS (pig)').one()
        resp = self._check(action='pig_fields', id=ds.id)
        self.assertItemsEqual(
            ['metric', 'opening', 'title'],
            [fld['column_name'] for fld in resp['fields']]
        )
        self.assertTrue("""metric:float
, opening:integer
, title:chararray""" in resp['sample'], resp['sample'])

    @mock_s3
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

    @mock_s3
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

class TestTasksTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the celery tasks.
    """
    datasets = [ImportHandlerData, DataSetData, ModelData, TestResultData]

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
