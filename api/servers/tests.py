import httplib
from moto.s3.models import FakeKey
from mock import patch, ANY
from moto import mock_s3, mock_dynamodb2
import boto

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from .fixtures import ServerData
from .models import Server
from .config import FOLDER_MODELS
from .views import ServerResource, ServerFileResource
from .tasks import upload_import_handler_to_server, upload_model_to_server
from api.import_handlers.fixtures import ImportHandlerData,\
    XmlImportHandlerData, XmlEntityData
from api.import_handlers.models import ImportHandler, XmlImportHandler,\
    XmlEntity
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.accounts.models import User


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
        self._check_object_with_fixture_class(server, ServerData.server_01)

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
    datasets = [ModelData, ImportHandlerData, XmlImportHandlerData,
                XmlEntityData, ServerData]

    def setUp(self):
        super(ServerFileResourceTests, self).setUp()
        self.server = Server.query.first()
        self.BASE_URL = self.BASE_URL.format(self.server.id, FOLDER_MODELS)

    #@patch('api.servers.models.Server.list_keys')
    #@mock_s3
    @patch('api.servers.tasks.logging')
    #@patch('api.amazon_utils.AmazonS3Helper.list_keys')
    def test_list(self, logging_mock):
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        user = User.query.first()
        upload_model_to_server(server.id, model.id, user.id)
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        #list_keys_mock.return_value = [key]
        resp_data = self._check()
        #self.assertTrue(list_keys_mock.called)
        self.assertTrue(key in resp_data, resp_data)
        self.assertTrue(len(resp_data[key]), 1)
        #print resp_data[key], key
        #raise

    def test_delete(self):
        pass

    def test_edit(self):
        pass

    def test_reload_on_predict(self):
        pass


class ServersTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [ModelData, ImportHandlerData, XmlImportHandlerData,
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

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    def test_upload_import_handler(self, uuid, mock_save_key_string):
        guid = '7686f8b8-dc26-11e3-af6a-20689d77b543'
        uuid.return_value = guid
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).one()
        user = User.query.first()

        upload_import_handler_to_server(server.id, ImportHandler.TYPE,
                                        handler.id, user.id)

        mock_save_key_string.assert_called_once_with(
            'odesk-match-cloudml/analytics/importhandlers/%s.json' % guid,
            ANY,
            {
                'id': handler.id,
                'name': handler.name,
                'object_name': handler.name,
                'type': handler.TYPE,
                'user_id': user.id,
                'user_name': user.name,
                'hide': "False",
                'uploaded_on': ANY
            }
        )

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    def test_upload_xml_import_handler(self, uuid, mock_save_key_string):
        guid = 'pbnehzuEQlGTeQO7I6P8_w'
        uuid.return_value = guid
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        handler = XmlImportHandler.query.filter_by(
            name=XmlImportHandlerData.xml_import_handler_01.name).one()
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
                'uploaded_on': ANY
            }
        )
