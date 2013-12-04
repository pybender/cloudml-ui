from mock import patch, Mock

from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.accounts.models import User

from views import InstanceResource
from models import Instance
from fixtures import InstanceData
from tasks import *


class InstancesTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Instances API.
    """
    BASE_URL = '/cloudml/aws_instances/'
    RESOURCE = InstanceResource
    Model = Instance
    datasets = [InstanceData, ]

    def test_list(self):
        resp = self.check_list(show='name,type')
        self.assertTrue(resp['instances'][0]['type'])
        self.assertTrue(resp['instances'][0]['name'])

    def test_details(self):
        instance = self.Model.query.filter_by(name='Instance 1')[0]
        resp = self.check_details(
            show='name,ip,is_default,type', obj=instance)
        instance_resp = resp['instance']
        self.assertEqual(instance_resp['name'], instance.name)
        self.assertEqual(instance_resp['type'], instance.type)
        self.assertEqual(instance_resp['ip'], instance.ip)
        self.assertEqual(instance_resp['is_default'], False)

    def test_post(self):
        post_data = {'ip': '1.1.1.1',
                     'type': 'small',
                     'name': 'new',
                     'is_default': 'false'}
        resp, obj = self.check_edit(post_data)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.ip, post_data['ip'])
        self.assertEqual(obj.type, post_data['type'])

        # Let's check posting new default instance
        obj.is_default = True
        obj.save()

        post_data['name'] = 'default'
        post_data['is_default'] = True
        resp, new_obj = self.check_edit(post_data)
        self.assertEqual(new_obj.name, post_data['name'])
        self.assertEqual(new_obj.ip, post_data['ip'])
        self.assertEqual(new_obj.type, post_data['type'])
        self.assertTrue(new_obj.is_default)

        obj = self.Model.query.filter_by(name='new').one()
        self.assertFalse(obj.is_default)

    def test_post_validation(self):
        self.check_edit_error(
            {'description': 'test instance'},
            errors={'ip': 'ip is required',
                    'type': 'type is required',
                    'name': 'name is required'})

    def test_put(self):
        instance = self.Model.query.filter_by(name='Instance 1')[0]
        data = {'ip': '12.12.12.12',
                'type': 'large',
                'name': 'new name',
                'is_default': 'true'}
        resp, obj = self.check_edit(data, id=instance.id)
        self.assertEqual(obj.name, data['name'])
        self.assertEqual(obj.ip, data['ip'])
        self.assertEqual(obj.type, data['type'])
        self.assertTrue(obj.is_default)

    def test_delete(self):
        instance = self.Model.query.filter_by(name='Instance 1')[0]
        self.check_delete(instance)


class TestInstanceTasks(BaseDbTestCase):
    datasets = [ModelData]

    # TODO: Investigate why we can't drop db in tearDown
    # mthd, when testing celery tasks
    def tearDown(self):
        pass

    def finish(self):
        self.db.session.remove()
        self.db.drop_all()

    """ Tests spot instances specific tasks """
    @patch('api.amazon_utils.AmazonEC2Helper.request_spot_instance',
           return_value=Mock(id='some_id')
           )
    def test_request_spot_instance(self, mock_request):
        model = Model.query.all()[0]
        res = request_spot_instance(
            'dataset_id', 'instance_type', model.id)

        model = Model.query.get(model.id)
        self.assertEquals(model.status, model.STATUS_REQUESTING_INSTANCE)
        self.assertEquals(res, 'some_id')
        self.assertEquals(model.spot_instance_request_id, res)
        self.finish()

    @patch('api.amazon_utils.AmazonEC2Helper.get_instance',
           return_value=Mock(**{'private_ip_address': '8.8.8.8'}))
    @patch('api.tasks.train_model')
    def test_get_request_instance(self, mock_get_instance, mock_train):
        model = Model.query.all()[0]
        user = User.query.all()[0]

        with patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance',
                   return_value=Mock(**{
                       'state': 'active',
                       'status.code': '200',
                       'status.message': 'Msg',
                   })):
            res = get_request_instance('some_id',
                         callback='train',
                         dataset_ids=['dataset_id'],
                         model_id=model.id,
                         user_id=user.id)
            self.assertEquals(res, '8.8.8.8')
            self.assertTrue(mock_train.apply_async)

            model = Model.query.get(model.id)
            self.assertEquals(model.status, model.STATUS_INSTANCE_STARTED)

    @patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance')
    def test_get_request_instance_failed(self, mock_request_instance):
        model = Model.query.all()[0]
        user = User.query.all()[0]

        mock_request_instance.return_value = Mock(**{
            'state': 'failed',
            'status.code': 'bad-parameters',
            'status.message': 'Msg',
        })

        self.assertRaises(
            InstanceRequestingError,
            get_request_instance,
            'some_id',
            callback='train',
            dataset_ids=['dataset_id'],
            model_id=model.id,
            user_id=user.id
        )

        model = Model.query.get(model.id)
        self.assertEquals(model.status, model.STATUS_ERROR)
        self.assertEquals(model.error, 'Instance was not launched')

    @patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance')
    def test_get_request_instance_canceled(self, mock_request_instance):
        model = Model.query.all()[0]
        user = User.query.all()[0]

        mock_request_instance.return_value = Mock(**{
            'state': 'canceled',
            'status.code': 'canceled',
            'status.message': 'Msg',
        })

        res = get_request_instance('some_id',
                         callback='train',
                         dataset_ids=['dataset_id'],
                         model_id=model.id,
                         user_id=user.id)
        self.assertIsNone(res)

        model = Model.query.get(model.id)
        self.assertEquals(model.status, model.STATUS_CANCELED)

    @patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance')
    def test_get_request_instance_still_open(self, mock_request_instance):
        from celery.exceptions import RetryTaskError

        model = Model.query.all()[0]
        user = User.query.all()[0]

        mock_request_instance.return_value = Mock(**{
            'state': 'open',
            'status.code': 'bad-parameters',
            'status.message': 'Msg',
        })

        self.assertRaises(
            RetryTaskError,
            get_request_instance,
            'some_id',
            callback='train',
            dataset_ids=['dataset_id'],
            model_id=model.id,
            user_id=user.id
        )

    @patch('api.amazon_utils.AmazonEC2Helper.terminate_instance')
    def test_terminate_instance(self, mock_terminate_instance):
        terminate_instance('some task id', 'some instance id')
        mock_terminate_instance.assert_called_with('some instance id')

    @patch('api.amazon_utils.AmazonEC2Helper.cancel_request_spot_instance')
    def test_cancel_request_spot_instance(self,
                                          mock_cancel_request_spot_instance):
        model = Model.query.all()[0]
        cancel_request_spot_instance('some req id', model.id)
        mock_cancel_request_spot_instance.assert_called_with('some req id')
        model = Model.query.get(model.id)
        self.assertEquals(model.status, model.STATUS_CANCELED)
