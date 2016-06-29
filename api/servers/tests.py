from datetime import datetime
from mock import patch, ANY, MagicMock
from api.amazon_utils import AmazonS3ObjectNotFound

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from .fixtures import ServerData, ServerModelVerificationData, \
    VerificationExampleData
from .models import Server, ServerModelVerification, VerificationExample
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS
from .views import ServerResource, ServerFileResource, \
    ServerModelVerificationResource, VerificationExampleResource
from .tasks import upload_import_handler_to_server, upload_model_to_server, \
    update_at_server, verify_model, VerifyModelTask
from api.import_handlers.fixtures import XmlImportHandlerData as \
    ImportHandlerData, XmlEntityData
from api.import_handlers.models import ImportHandler, XmlImportHandler,\
    XmlEntity
from api.ml_models.fixtures import ModelData, MODEL_TRAINER, SegmentData
from api.model_tests.fixtures import TestExampleData
from api.import_handlers.fixtures import get_importhandler
from api.ml_models.models import Model
from api.model_tests.models import TestExample
from api.accounts.models import User
from api.servers.grafana import GrafanaHelper
import json
from cloudml.trainer.store import TrainerStorage


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
    datasets = [ServerData, ModelData]

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

    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    @patch('api.servers.models.Server.list_keys')
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch.object(GrafanaHelper, 'model2grafana')
    def test_get_models_action(self, grafana_mock, save_mock, list_mock,
                               load_mock):
        # no models and import handlers
        list_mock.return_value = []
        result = self._check(server=self.obj.id, id=self.obj.id,
                             action='models')
        self.assertEqual(0, len(result['files']))

        # should return model data
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        model.trainer = 'trainer_file'
        model.train_import_handler = get_importhandler()
        model.test_import_handler = get_importhandler()
        model.name = 'BestMatch.v31'
        model.save()
        user = User.query.first()
        upload_model_to_server(self.obj.id, model.id, user.id)
        upload_import_handler_to_server(self.obj.id, 'xml',
                                        model.test_import_handler.id, user.id)

        def list_side_effect(*args, **kwargs):
            side_effect_data = {
                FOLDER_MODELS: [
                    {
                        'id': str(model.id),
                        'object_name': model.name,
                        'object_id': str(model.id),
                        'name': model.name,
                        'user_id': user.id,
                        'user_name': user.name,
                    }
                ],
                FOLDER_IMPORT_HANDLERS: [
                    {
                        'id': str(model.test_import_handler.id),
                        'object_name': model.test_import_handler.name,
                        'size': 100,
                        'name': model.test_import_handler.name,
                        'object_id': str(model.test_import_handler.id),
                        'object_type': model.test_import_handler.type,
                        'user_id': user.id,
                        'user_name': user.name,
                        'crc32': 'crc32'
                    }
                ]}
            if 'folder' in kwargs:
                return side_effect_data[kwargs['folder']]
            else:
                return []

        list_mock.side_effect = list_side_effect
        result = self._check(server=self.obj.id, id=self.obj.id,
                             action='models')
        self.assertEqual(1, len(result['files']))
        f = result['files'][0]
        self.assertEqual(f['model_name'], 'BestMatch.v31')
        self.assertEqual(f['model_metadata']['name'], 'BestMatch.v31')
        self.assertEqual(f['model']['id'], model.id)
        self.assertEqual(f['import_handler_name'],
                         f['import_handler_metadata']['name'])
        self.assertEqual(f['import_handler_metadata']['object_id'],
                         str(model.test_import_handler.id))
        self.assertEqual(f['import_handler']['id'],
                         model.test_import_handler.id)


class ServerFileResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Servers API.
    """
    SHOW = 'name,ip,folder'
    BASE_URL = '/cloudml/servers/{0!s}/files/{1!s}/'
    RESOURCE = ServerFileResource
    datasets = [ModelData, ImportHandlerData,
                XmlEntityData, ServerData]

    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    @patch('api.amazon_utils.AmazonS3Helper.list_keys')
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch.object(GrafanaHelper, 'model2grafana')
    def setUp(self, grafana_mock, save_mock, list_mock, load_mock):
        super(ServerFileResourceTests, self).setUp()
        self.server = Server.query.first()
        self.BASE_URL = self.BASE_URL.format(self.server.id, FOLDER_MODELS)
        self.model = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.model.trainer = 'trainer_file'
        self.user = User.query.first()
        upload_model_to_server(self.server.id, self.model.id, self.user.id)
        self.assertTrue(grafana_mock.called)

    def test_invalid_folder(self):
        base_url = '/cloudml/servers/{0!s}/files/{1!s}/'
        url = base_url.format(self.server.id, 'invalid_folder1')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEqual(resp.status_code, 404)

    @patch('api.servers.models.Server.list_keys')
    @patch('api.servers.tasks.logging')
    def test_list(self, logging_mock, list_mock):
        list_mock.return_value = [{'id': str(self.model.id),
                                   'name': self.model.name}]
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        resp_data = self._check()
        self.assertTrue(key in resp_data, resp_data)
        self.assertTrue(len(resp_data[key]), 1)

    @patch('api.amazon_utils.AmazonS3Helper.set_key_metadata')
    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    @patch('api.servers.models.Server.list_keys')
    @patch('api.servers.tasks.update_at_server')
    def test_delete(self, mock_update_at_server, list_mock, load_mock,
                    set_meta):
        self.model.servers_ids = [self.server.id]
        self.model.save()
        load_mock.return_value = {'Metadata': {'id': self.model.id}}
        list_mock.return_value = [{'id': str(self.model.id)}]
        files_list = [f for f in self.server.list_keys(FOLDER_MODELS)]
        obj_id = files_list[0]['id']

        # correct data
        url = '{0}{1}/'.format(self.BASE_URL, obj_id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(204, resp.status_code)
        self.assertTrue(mock_update_at_server.delay.called)
        self.assertTrue(self.server.id not in self.model.servers_ids)

        # non-existing
        set_meta.side_effect = AmazonS3ObjectNotFound('not found')
        url = '{0}{1}/'.format(self.BASE_URL, 'bbb.model')
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(404, resp.status_code)
        self.assertIn('not found', resp.data)


    @patch('api.amazon_utils.AmazonS3Helper.set_key_metadata')
    @patch('api.servers.models.Server.list_keys')
    @patch('api.servers.tasks.update_at_server')
    def test_edit(self, mock_update_at_server, list_mock, set_meta):
        # set Up
        model2 = Model.query.filter_by(name=ModelData.model_02.name).one()
        model2.trainer = 'trainer_file2'
        list_mock.return_value = [
            {'id': str(self.model.id), 'name': self.model.name},
            {'id': str(model2.id), 'name': model2.name}]
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
        set_meta.side_effect = AmazonS3ObjectNotFound('not found')
        url = '{0}{1}/'.format(self.BASE_URL, 'bbb.model')
        resp = self.client.put(url, data={'name': 'nnn'}, headers=HTTP_HEADERS)
        self.assertEqual(404, resp.status_code)
        self.assertIn('not found', resp.data)

    @patch('api.servers.models.Server.list_keys')
    @patch('api.servers.tasks.update_at_server')
    def test_reload_on_predict(self, mock_update_at_server, list_mock):
        list_mock.return_value = [{'id': str(self.model.id)}]
        files_list = [f for f in self.server.list_keys(FOLDER_MODELS)]
        obj_id = files_list[0]['id']
        url = self._get_url(id=obj_id, action='reload')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(mock_update_at_server.delay.called)


class ServersTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [ModelData, ImportHandlerData,
                XmlEntityData, ServerData, ServerModelVerificationData]

    @patch('api.servers.models.Server.list_keys')
    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    @patch.object(GrafanaHelper, 'model2grafana')
    def test_upload_model(self, grafana_mock, uuid, mock_save_key_string,
                          load_mock, list_mock):
        guid = '7686f8b8-dc26-11e3-af6a-20689d77b543'
        uuid.return_value = guid
        list_mock.return_value = []
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        user = User.query.first()

        upload_model_to_server(server.id, model.id, user.id)

        self.assertTrue(grafana_mock.called)
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
        self.assertTrue(server.id in model.servers_ids)

    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    @patch('api.servers.models.Server.list_keys')
    @patch.object(GrafanaHelper, 'model2grafana')
    def test_upload_model_existing_name(self, grafana_mock, list_keys, uuid,
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

        self.assertFalse(grafana_mock.called)
        self.assertFalse(mock_save_key_string.called)

    @patch('api.servers.models.Server.list_keys')
    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('api.servers.tasks.get_a_Uuid')
    def test_upload_import_handler(self, uuid, mock_save_key_string,
                                   list_mock):
        guid = 'pbnehzuEQlGTeQO7I6P8_w'
        uuid.return_value = guid
        list_mock.return_value = []
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        handler = XmlImportHandler.query.filter_by(
            name=ImportHandlerData.import_handler_01.name).one()
        handler.servers_ids = []
        handler.save()
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
        self.assertTrue(server.id in handler.servers_ids)
        self.assertEqual(handler.server_type, server.type)
        self.assertEqual(handler.servers[0].name, server.name)

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

    @patch('api.servers.tasks.VerifyModelTask.run')
    def test_verify_model_task(self, verify_task):
        verification = ServerModelVerification.query.first()
        verify_model(verification.id, 2)
        verify_task.assert_called_once_with(verification.id, 2)


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

        key_obj = {}
        key_obj['Metadata'] = self.METADATA_MAP
        key_obj['ContentLength'] = 123321
        key_obj['LastModified'] = datetime(2014, 8, 6, 23, 46, 48)

        two_key = MagicMock()
        two_key.name = \
            'odesk-match-cloudml/analytics/models/n3sz3FTFQJeUOe33VF2B.model'

        s3_mock = MagicMock()
        s3_mock.list_keys.return_value = [{'Key': one_key.name}]
        s3_mock.load_key.return_value = key_obj

        helper_mock.return_value = s3_mock

        objs = server.list_keys()

        s3_mock.load_key.assert_called_with(one_key.name, with_metadata=True)

        self.assertEqual(1, len(objs))
        obj = objs[0]
        self.assertListEqual(
            obj.keys(),
            ['uploaded_on', 'object_type', 'last_modified', 'crc32',
             'id', 'size', 'server_id', 'user_id', 'name', 'object_id',
             'object_name', 'user_name'])
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

        # sort by id
        s3_mock.list_keys.return_value = [{'Key': one_key.name},
            {'Key': two_key.name}]
        helper_mock.return_value = s3_mock
        params = {'sort_by': 'id', 'order': 'desc'}
        objs = server.list_keys(folder=None, params=params)

        self.assertEqual(2, len(objs))
        self.assertEqual('n3sz3FTFQJeUOe33VF2B.model', objs[0]['id'])
        self.assertEqual('n3sz3FTFQJeUOe33VF2A.model', objs[1]['id'])

        # sort by non-existing field
        params = {'sort_by': 'my_id', 'order': 'desc'}
        self.assertRaises(ValueError, server.list_keys, None, params)

# Verification Related Tests


class VerifyModelTaskTests(BaseDbTestCase, TestChecksMixin):
    datasets = [ServerModelVerificationData, VerificationExampleData, TestExampleData]

    def setUp(self):
        super(VerifyModelTaskTests, self).setUp()
        self.verify_model_task = VerifyModelTask()
        self.verification = ServerModelVerification.query.first()
        self.verify_model_task.verification = self.verification

    def test_get_verification(self):
        self.assertRaises(ValueError,
                          self.verify_model_task.get_verification, 0)
        self.assertEqual(1, len(VerificationExample.query.filter(
            VerificationExample.verification_id == self.verification.id).all())
        )
        ver = self.verify_model_task.get_verification(self.verification.id)
        self.assertEqual(ServerModelVerification.STATUS_IN_PROGRESS,
                         ver.status)
        self.assertEqual({}, ver.result)
        self.assertEqual(0, len(VerificationExample.query.filter(
            VerificationExample.verification_id == ver.id).all()))

    def test_create_example_error(self):
        test_example = TestExample.query.first()
        self.verify_model_task.create_example_err(test_example, 'Some error',
                                                  'Some data')

        examples = VerificationExample.query.filter_by(
            verification_id=self.verification.id).all()
        self.assertEqual(2, len(examples))
        self.assertEqual(examples[1].result, {
            'message': 'Error sending data to predict',
            'error': 'Some error',
            'status': 'Error',
            '_data': 'Some data'
        })

    def test_importhandler_property(self):
        self.assertEqual('my_import_handler',
                         self.verify_model_task.importhandler)

        self.verification.description = {}
        self.verification.save()
        with self.assertRaises(ValueError):
            ih = self.verify_model_task.importhandler

    def test_prepare_example_data(self):
        self.verification.params_map = {}
        test_example = TestExample.query.first()
        self.assertEqual({},
                         self.verify_model_task.prepare_example_data(
                             test_example))

        self.verification.params_map = u'{"country": "employer.country"}'
        self.assertEqual({"country": "USA"},
                         self.verify_model_task.prepare_example_data(
                             test_example))

    def test_predict_property(self):
        predict = self.verify_model_task.predict
        self.assertEqual(predict.cloudml_url, 'http://127.0.0.1/cloudml')

    @patch('predict.libpredict.Predict.post_to_cloudml')
    @patch('predict.command.bestmatch.BestmatchPredictCommand.call')
    def test_call_predict_command(self, bestmatch_mock, predict_post_mock):
        example = TestExample.query.filter_by(
            test_result=self.verification.test_result).limit(1)
        data = self.verify_model_task.prepare_example_data(example[0])
        res = self.verify_model_task.call_predict_command(data)
        predict_post_mock.assert_called_once_with('v3', 'my_import_handler',
                                                  None, data, throw_error=True,
                                                  saveResponseTime=True)

        self.verification.clazz = 'predict.command.bestmatch.' \
                                  'BestmatchPredictCommand'
        res = self.verify_model_task.call_predict_command(data)
        bestmatch_mock.assert_called_once_with([
            'run.py', '-c', self.verify_model_task.get_config_file(), '-i',
            'my_import_handler', '-p', 'v3', '-a', '201913099'])

    def test_process(self):
        self.verify_model_task.process(3)
        self.assertEqual({
            u'count': 3,
            u'valid_count': 0,
            u'zero_features': [u'hire_outcome', u'application_id'],
            u'max_response_time': 0,
            u'valid_prob_count': 0,
            u'error_count': 3}, self.verification.result)
        self.assertEqual(ServerModelVerification.STATUS_DONE,
                         self.verification.status)

    @patch('api.servers.tasks.VerifyModelTask.process')
    def test_run_exception(self, process_mock):
        process_mock.side_effect = Exception('Some exception')
        self.assertRaises(Exception, self.verify_model_task.run,
                          self.verification.id, 3)
        self.assertEqual(ServerModelVerification.STATUS_ERROR,
                         self.verification.status)
        self.assertEqual('Some exception', self.verification.error)

    @patch('api.servers.tasks.VerifyModelTask.process')
    def test_run(self, process_mock):
        self.verify_model_task.run(self.verification.id, 3)
        process_mock.assert_called_once_with(3)


class ServerModelVerificationResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Server Model Verification API.
    """
    SHOW = 'status,params_map,error'
    BASE_URL = '/cloudml/servers/verifications/'
    RESOURCE = ServerModelVerificationResource
    datasets = [ServerData, ServerModelVerificationData]

    def setUp(self):
        super(ServerModelVerificationResourceTests, self).setUp()
        self.obj = self.Model.query.first()

    def test_list(self):
        resp = self.check_list(show=self.SHOW)
        model = self._get_resp_object(resp)
        self._check_object_with_fixture_class(
            model,
            ServerModelVerificationData.model_verification_01)

    def test_details(self):
        self.check_details(
            show=self.SHOW,
            fixture_cls=ServerModelVerificationData.model_verification_01)

    def test_verify_action(self):
        url = self._get_url(
            id=self.obj.id, action='verify')
        resp = self.client.put(
            url, data={'count': 5}, headers=HTTP_HEADERS)
        result = json.loads(resp.data)
        self.assertEqual(
            ServerModelVerification.STATUS_DONE, result['status'])
        model = result['server_model_verification']
        self.assertEqual(
            ServerModelVerification.STATUS_DONE,
            model['status'])

    def test_get_predict_classes_action(self):
        url = self._get_url(id=self.obj.id, action='predict_classes')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        result = json.loads(resp.data)
        self.assertTrue('classes' in result.keys())


class GrafanaTests(BaseDbTestCase):
    datasets = [ServerData, ModelData]

    def setUp(self):
        super(GrafanaTests, self).setUp()
        self.server = Server.query.first()
        self.model = Model.query.first()

    def test_model2grafana(self):
        def _check(get_dashboard_mock,
                   post_dashboard_mock, old_dashboard_json):
            get_dashboard_mock.return_value = {'dashboard': old_dashboard_json}
            post_dashboard_mock.return_value = {}
            result = helper.model2grafana(self.model)
            self.assertTrue(get_dashboard_mock.called,
                            'Should try to get server dashboard')
            self.assertTrue(post_dashboard_mock.called,
                            'Should update server dashboard')
            get_dashboard_mock.reset_mock()
            post_dashboard_mock.reset_mock()
            return result

        helper = GrafanaHelper(self.server)

        with patch('grafana_api_client.DeferredClientRequest.get') as mock:
            with patch('grafana_api_client.DeferredClientRequest.create') \
                    as post_mock:
                # dashboard does not exist
                from grafana_api_client import GrafanaClientError
                mock.side_effect = GrafanaClientError()
                result = _check(mock, post_mock, {})
                self.assertEqual(result['title'],
                                 'CloudMl {}'.format(self.server.name),
                                 'Server dashboard should be added')
                self.assertEquals(len(result['rows']), 1)
                self.assertEqual(result['rows'][0]['title'], self.model.name)
                mock.side_effect = None

                # dashboard exist, model exist
                dashboard = helper._create_dashboard_json()
                dashboard['title'] += '-old'
                model_json = helper._get_model_json(self.model)
                model_json['old_title'] = 'old-model-name'
                dashboard['rows'].append(model_json)

                result = _check(mock, post_mock, dashboard)
                self.assertEqual(
                    result['title'],
                    'CloudMl {}-old'.format(self.server.name),
                    'Server dashboard should not be replaced {}'.format(
                        result['title']))
                self.assertEquals(len(result['rows']), 1)
                self.assertEqual(result['rows'][0]['title'], self.model.name)
                self.assertFalse('old_title' in result['rows'][0])

                # dashboard exist, model does not exist
                OTHER_MODEL = 'other-model'
                dashboard = helper._create_dashboard_json()
                dashboard['title'] += '-old'
                model_json = helper._get_model_json(self.model)
                model_json['title'] = OTHER_MODEL
                dashboard['rows'].append(model_json)

                result = _check(mock, post_mock, dashboard)
                self.assertEqual(result['title'],
                                 'CloudMl {}-old'.format(self.server.name),
                                 'Server dashboard should not be replaced')
                self.assertEquals(len(result['rows']), 2)
                self.assertEqual(result['rows'][0]['title'], OTHER_MODEL)
                self.assertEqual(result['rows'][1]['title'], self.model.name)


class VerificationExampleResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Server Model Verification API.
    """
    SHOW = 'result'
    BASE_URL = '/cloudml/servers/verifications/{0!s}/examples/'
    RESOURCE = VerificationExampleResource
    datasets = [ServerModelVerificationData, VerificationExampleData,
                SegmentData]

    def setUp(self):
        super(VerificationExampleResourceTests, self).setUp()
        verification = ServerModelVerification.query.first()
        self.BASE_URL = self.BASE_URL.format(verification.id)
        self.obj = self.Model.query.first()


    def test_list(self):
        resp = self.check_list(show=self.SHOW)
        model = self._get_resp_object(resp)
        self._check_object_with_fixture_class(
            model,
            VerificationExampleData.verification_example_01)

    @patch('api.ml_models.models.Model.get_trainer')
    def test_details(self, mock_get_trainer):
        trainer = TrainerStorage.loads(MODEL_TRAINER)
        mock_get_trainer.return_value = trainer
        self.check_details(
            show=self.SHOW,
            fixture_cls=VerificationExampleData.verification_example_01)
        self.assertTrue(self.obj.example.weighted_data_input)

        # with existing weighted data input
        self.check_details(
            show=self.SHOW,
            fixture_cls=VerificationExampleData.verification_example_01)

