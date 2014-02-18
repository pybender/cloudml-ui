from mock import patch, ANY
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase
from .fixtures import ServerData
from .models import Server
from .tasks import upload_import_handler_to_server, upload_model_to_server
from api.import_handlers.fixtures import ImportHandlerData
from api.import_handlers.models import ImportHandler
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.accounts.models import User


class ServersTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [ModelData, ImportHandlerData, ServerData]

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    def test_upload_model(self, mock_save_key_string):
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        user = User.query.first()

        upload_model_to_server(server.id, model.id, user.id)

        mock_save_key_string.assert_called_once_with(
            'odesk-match-cloudml/analytics/models/TrainedModel.model',
            ANY,
            {
                'model_id': model.id,
                'user_id': user.id,
                'model_name': 'TrainedModel',
                'user_name': 'User-1',
                'uploaded_on': ANY,
            }
        )

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    def test_upload_import_handler(self, mock_save_key_string):
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        handler = ImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).one()
        user = User.query.first()

        upload_import_handler_to_server(server.id, handler.id, user.id)

        mock_save_key_string.assert_called_once_with(
            'odesk-match-cloudml/analytics/importhandlers/Handler 1.json',
            ANY,
            {
                'handler_id': handler.id,
                'user_id': user.id,
                'handler_name': 'Handler 1',
                'user_name': 'User-1',
                'uploaded_on': ANY,
            }
        )
