from datetime import datetime

from mock import patch, ANY, MagicMock
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


class ServerModelTests(BaseDbTestCase):

    datasets = [ServerData]

    @patch('api.servers.models.AmazonS3Helper')
    def test_list_keys(self, helper_mock):

        def get_metadata(meta):
            if meta == 'object_name':
                return 'prod_405_again'
            elif meta == 'uploaded_on':
                return '2014-08-06 23:38:56.081141'
            elif meta == 'name':
                return 'prod_405_again'
            elif meta == 'id':
                return '30'
            elif meta == 'type':
                return None
            elif meta == 'user_id':
                return '1'
            elif meta == 'user_name':
                return 'Nader Soliman'
            elif meta == 'hide':
                False
            else:
                msg = 'unexpected call to get_metadata with %s please expand '
                'the test', meta
                raise Exception(msg)

        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        one_key = MagicMock()
        one_key.name = 'odesk-match-cloudml/analytics/models/n3sz3FTFQJeUOe33VF2A.model'

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
        self.assertEqual(set(obj.keys()),
                         {'id', 'object_name', 'size', 'last_modified', 'name',
                          'uploaded_on', 'object_id', 'object_type', 'user_id',
                          'user_name', 'server_id'})
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
