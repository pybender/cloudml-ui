import httplib
from moto.s3.models import FakeKey
from mock import patch, ANY
from moto import mock_s3, mock_dynamodb2
import boto
from datetime import datetime
from mock import patch, ANY, MagicMock

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from .fixtures import ServerData
from .models import Server
from .config import FOLDER_MODELS
from .views import ServerResource, ServerFileResource
from .tasks import upload_import_handler_to_server, upload_model_to_server, \
    update_at_server
from api.import_handlers.fixtures import XmlImportHandlerData as \
    ImportHandlerData, XmlEntityData
from api.import_handlers.models import ImportHandler, XmlImportHandler,\
    XmlEntity
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.accounts.models import User
import json


class ServerModelTests(BaseDbTestCase):
    datasets = [ServerData]

    def test_server_is_default(self):
        srv = Server.query.filter_by(is_default=False)[0]
        srv.is_default = True
        srv.save()

        db.session.refresh(srv)

        self.assertTrue(srv.is_default)
        defaults = Server.query.filter_by(is_default=True)
        self.assertEquals(defaults.count(), 1, list(defaults))


class ServerResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Servers API.
    """
    SHOW = 'name,ip,folder'
    BASE_URL = '/cloudml/servers/'
    RESOURCE = ServerResource
    datasets = [ServerData]

    def setUp(self):
        super(ServerResourceTests, self).setUp()
        self.obj = self.Model.query.first()

    def test_list(self):
        resp = self.check_list(show=self.SHOW)
        server = self._get_resp_object(resp)
        self._check_object_with_fixture_class(server, ServerData.server_02)

    def test_details(self):
        self.check_details(show=self.SHOW, fixture_cls=ServerData.server_01)

    def test_readonly(self):
        self.check_readonly()


class ServerFileResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Servers API.
    """
    SHOW = 'name,ip,folder'
    BASE_URL = '/cloudml/servers/{0!s}/files/{1!s}/'
    RESOURCE = ServerFileResource
    datasets = [ModelData, ImportHandlerData,
                XmlEntityData, ServerData]

    @mock_s3
    def setUp(self):
        super(ServerFileResourceTests, self).setUp()
        self.server = Server.query.first()
        self.BASE_URL = self.BASE_URL.format(self.server.id, FOLDER_MODELS)
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        model.trainer = 'trainer_file'
        self.user = User.query.first()
        upload_model_to_server(self.server.id, model.id, self.user.id)

    # def test_invalid_folder(self):
    #     url = self.BASE_URL.format(self.server.id, 'invalid_folder1')
    #     resp = self.client.get(url, headers=HTTP_HEADERS)
    #     self.assertEqual(resp.status_code, 404)

    # @patch('api.servers.models.Server.list_keys')
    # @mock_s3
    @patch('api.servers.tasks.logging')
    # @patch('api.amazon_utils.AmazonS3Helper.list_keys')
    def test_list(self, logging_mock):
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        resp_data = self._check()
        self.assertTrue(key in resp_data, resp_data)
        self.assertTrue(len(resp_data[key]), 1)

    @patch('api.servers.tasks.update_at_server')
    def test_delete(self, mock_update_at_server):
        files_list = [f for f in self.server.list_keys(FOLDER_MODELS)]
        obj_id = files_list[0]['id']

        # correct data
        url = '{0}{1}/'.format(self.BASE_URL, obj_id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(204, resp.status_code)
        self.assertTrue(mock_update_at_server.delay.called)
        self.assertEqual(0, len(self.server.list_keys(FOLDER_MODELS)))

        # non-existing
        url = '{0}{1}/'.format(self.BASE_URL, 'bbb.model')
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(404, resp.status_code)
        self.assertIn('not found', resp.data)

    @patch('api.servers.tasks.update_at_server')
    def test_edit(self, mock_update_at_server):
        # set Up
        model2 = Model.query.filter_by(name=ModelData.model_02.name).one()
        model2.trainer = 'trainer_file2'
        upload_model_to_server(self.server.id, model2.id, self.user.id)
        # make order
        files_list = [f for f in self.server.list_keys(FOLDER_MODELS)]
        obj_id = files_list[0]['id']

        url = '{0}{1}/'.format(self.BASE_URL, obj_id)
        # correct data
        resp = self.client.put(url, data={'name': 'new name'},
                               headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(mock_update_at_server.delay.called)
        resp_data = json.loads(resp.data)
        self.assertEqual(obj_id, resp_data[self.RESOURCE.OBJECT_NAME]['id'])

        # test edit with same name
        resp = self.client.put(url, data={'name': files_list[1]['name']},
                               headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn('already exists on the server', resp.data)

        # non-existing
        url = '{0}{1}/'.format(self.BASE_URL, 'bbb.model')
        resp = self.client.put(url, data={'name': 'nnn'}, headers=HTTP_HEADERS)
        self.assertEqual(404, resp.status_code)
        self.assertIn('not found', resp.data)

    @patch('api.servers.tasks.update_at_server')
    def test_reload_on_predict(self, mock_update_at_server):
        files_list = [f for f in self.server.list_keys(FOLDER_MODELS)]
        obj_id = files_list[0]['id']
        url = self._get_url(id=obj_id, action='reload')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(mock_update_at_server.delay.called)


class ServersTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [ModelData, ImportHandlerData,
                XmlEntityData, ServerData]

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    def test_upload_model(self, uuid, mock_save_key_string):
        guid = '7686f8b8-dc26-11e3-af6a-20689d77b543'
        uuid.return_value = guid
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        user = User.query.first()

        upload_model_to_server(server.id, model.id, user.id)

        mock_save_key_string.assert_called_once_with(
            'odesk-match-cloudml/analytics/models/%s.model' % guid,
            ANY,
            {
                'id': model.id,
                'object_name': model.name,
                'name': model.name,
                'user_id': user.id,
                'user_name': user.name,
                'hide': "False",
                'uploaded_on': ANY
            }
        )
        self.assertTrue(model.locked)
        self.assertTrue(model.features_set.locked)
        for ds in model.datasets:
            self.assertTrue(ds.locked)

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    @patch('api.servers.models.Server.list_keys')
    def test_upload_model_existing_name(self, list_keys, uuid,
                                        mock_save_key_string):
        guid = '7686f8b8-dc26-11e3-af6a-20689d77b543'
        uuid.return_value = guid
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        user = User.query.first()

        list_keys.return_value = [{
            'id': 'uid',
            'object_name': model.name,
            'size': 100,
            'name': model.name,
            'object_id': model.id,
            'object_type': 'model',
            'user_id': user.id,
            'user_name': user.name,
            'crc32': 'crc32',
            'server_id': server.id}]

        with self.assertRaises(ValueError):
            upload_model_to_server(server.id, model.id, user.id)

        self.assertFalse(mock_save_key_string.called)

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    def test_upload_import_handler(self, uuid, mock_save_key_string):
        guid = 'pbnehzuEQlGTeQO7I6P8_w'
        uuid.return_value = guid
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        handler = XmlImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).one()
        user = User.query.first()

        upload_import_handler_to_server(server.id, XmlImportHandler.TYPE,
                                        handler.id, user.id)

        mock_save_key_string.assert_called_once_with(
            'odesk-match-cloudml/analytics/importhandlers/%s.xml' % guid,
            ANY,
            {
                'id': handler.id,
                'name': handler.name,
                'object_name': handler.name,
                'type': handler.TYPE,
                'user_id': user.id,
                'user_name': user.name,
                'hide': "False",
                'uploaded_on': ANY,
                'crc32': '0x4FAF0BAA'  # TODO: '0xC8AD8D64'
            }
        )
        self.assertTrue(handler.locked)

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    @patch('api.servers.models.Server.list_keys')
    def test_upload_import_handler_existing_name(self, list_keys, uuid,
                                                 mock_save_key_string):
        guid = 'pbnehzuEQlGTeQO7I6P8_w'
        uuid.return_value = guid
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        handler = XmlImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).one()
        user = User.query.first()
        list_keys.return_value = [{
            'id': 'uid',
            'object_name': handler.name,
            'size': 100,
            'name': handler.name,
            'object_id': handler.id,
            'object_type': handler.TYPE,
            'user_id': user.id,
            'user_name': user.name,
            'crc32': 'crc32',
            'server_id': server.id}]

        with self.assertRaises(ValueError):
            upload_import_handler_to_server(
                server.id, XmlImportHandler.TYPE,
                handler.id, user.id)


class ServerModelTests(BaseDbTestCase):

    datasets = [ServerData]
    METADATA_MAP = {
        'object_name': 'prod_405_again',
        'uploaded_on': '2014-08-06 23:38:56.081141',
        'name': 'prod_405_again',
        'id': '30',
        'user_id': '1',
        'user_name': 'Nader',
        'type': None,
        'hide': False,
        'crc32': 'crc32'
    }

    @patch('api.servers.models.AmazonS3Helper')
    def test_list_keys(self, helper_mock):

        def get_metadata(meta):
            try:
                return self.METADATA_MAP[meta]
            except KeyError:
                raise Exception("unexpected call to get_metadata with %s \
                    please expand the test" % meta)

        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        one_key = MagicMock()
        one_key.name = \
            'odesk-match-cloudml/analytics/models/n3sz3FTFQJeUOe33VF2A.model'

        key_obj = MagicMock()
        key_obj.get_metadata = get_metadata
        key_obj.size = 123321
        key_obj.last_modified = 'Wed, 06 Aug 2014 23:46:48 GMT'

        s3_mock = MagicMock()
        s3_mock.list_keys.return_value = [one_key]
        s3_mock.bucket.get_key.return_value = key_obj

        helper_mock.return_value = s3_mock

        objs = server.list_keys()

        s3_mock.bucket.get_key.assert_called_with(one_key.name)

        self.assertEqual(1, len(objs))
        obj = objs[0]
        self.assertListEqual(
            obj.keys(),
            ['uploaded_on', 'object_type', 'last_modified', 'crc32',
             'id', 'size', 'server_id', 'user_id', 'name', 'object_id',
             'object_name', 'user_name'])
        # just test we can parse the datetime
        datetime.strptime(obj['last_modified'], '%Y-%m-%d %H:%M:%S')
        self.assertEqual(obj['id'], 'n3sz3FTFQJeUOe33VF2A.model')
        self.assertEqual(obj['object_name'], get_metadata('object_name'))
        self.assertEqual(obj['size'], 123321)
        self.assertEqual(obj['uploaded_on'], get_metadata('uploaded_on'))
        self.assertEqual(obj['last_modified'], '2014-08-06 23:46:48')
        self.assertEqual(obj['uploaded_on'], get_metadata('uploaded_on'))
        self.assertEqual(obj['name'], get_metadata('name'))
        self.assertEqual(obj['object_id'], get_metadata('id'))
        self.assertEqual(obj['object_type'], None)
        self.assertEqual(obj['user_id'], get_metadata('user_id'))
        self.assertEqual(obj['user_name'], get_metadata('user_name'))
        self.assertEqual(obj['server_id'], server.id)
