from mock import patch, ANY
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase
from .fixtures import ServerData
from .models import Server
from .tasks import upload_import_handler_to_server, upload_model_to_server
from api.import_handlers.fixtures import ImportHandlerData,\
    XmlImportHandlerData, XmlEntityData
from api.import_handlers.models import ImportHandler, XmlImportHandler,\
    XmlEntity
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.accounts.models import User


class ServersTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [ModelData, ImportHandlerData, XmlImportHandlerData,
                XmlEntityData, ServerData]

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('uuid.uuid1')
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
    @patch('uuid.uuid1')
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
    @patch('uuid.uuid1')
    def test_upload_xml_import_handler(self, uuid, mock_save_key_string):
        guid = '7686f8b8-dc26-11e3-af6a-20689d77b543'
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
