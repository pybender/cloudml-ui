# Authors: Nikolay Melnik <nmelnik@upwork.com>

import httplib
from mock import patch, Mock

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, \
    DefaultsCheckMixin, HTTP_HEADERS
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model
from api.accounts.models import User
from api.features.fixtures import FeatureSetData, FeatureData

from views import InstanceResource, ClusterResource
from models import Instance, Cluster
from fixtures import InstanceData, ClusterData, ACTIVE_CLUSTERS_COUNT
from tasks import *
from api.tasks import TRAIN_MODEL_TASK
from api.base.models import db
from api.base.exceptions import CloudmlUIValueError


class InstanceModelTests(BaseDbTestCase, DefaultsCheckMixin):
    datasets = [InstanceData]

    def test_set_default(self):
        self._check_is_default(Instance)


class InstancesTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Instances API.
    """
    BASE_URL = '/cloudml/aws_instances/'
    RESOURCE = InstanceResource
    datasets = [InstanceData, ]

    def test_list(self):
        self.check_list(show='name,type')

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
    datasets = [FeatureData, FeatureSetData, ModelData, ClusterData]

    # TODO: Investigate why we can't drop db in tearDown
    # mthd, when testing celery tasks
    # def tearDown(self):
    #     pass

    def finish(self):
        pass
        # self.db.session.remove()
        # self.db.drop_all()

    """ Tests spot instances specific tasks """
    @patch('api.amazon_utils.AmazonEC2Helper.request_spot_instance',
           return_value=Mock(id='some_id')
           )
    def test_request_spot_instance(self, mock_request):
        model = Model.query.all()[0]
        res = request_spot_instance('instance_type', model.id)

        model = Model.query.get(model.id)
        self.assertEquals(model.status, model.STATUS_REQUESTING_INSTANCE)
        self.assertEquals(res, 'some_id')
        self.assertEquals(model.spot_instance_request_id, res)
        self.finish()

    @patch('api.amazon_utils.AmazonEC2Helper.get_instance',
           return_value=Mock(**{'private_ip_address': '8.8.8.8'}))
    @patch('api.ml_models.tasks.train_model')
    def test_get_request_instance(self, mock_get_instance, mock_train):
        model = Model.query.all()[0]
        user = User.query.all()[0]

        with patch(
            'api.amazon_utils.AmazonEC2Helper.get_request_spot_instance',
            return_value=Mock(**{'state': 'active',
                                 'status.code': '200',
                                 'status.message': 'Msg'})):
            res = get_request_instance(
                'some_id',
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

        res = get_request_instance(
            'some_id',
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
        terminate_instance('some instance id')
        mock_terminate_instance.assert_called_with('some instance id')

    @patch('api.amazon_utils.AmazonEC2Helper.cancel_request_spot_instance')
    def test_cancel_request_spot_instance(self,
                                          mock_cancel_request_spot_instance):
        model = Model.query.all()[0]
        cancel_request_spot_instance('some req id', model.id)
        mock_cancel_request_spot_instance.assert_called_with('some req id')
        model = Model.query.get(model.id)
        self.assertEquals(model.status, model.STATUS_CANCELED)

    @patch('subprocess.Popen')
    def test_run_ssh_tunnel(self, popen):
        cluster = Cluster.query.first()
        run_ssh_tunnel(cluster.id)
        # popen.assert_called_with('dfsdf')


# ==== Clusters ====

class ClusterModelTest(BaseDbTestCase):
    datasets = [ClusterData]

    def test_generate_port(self):
        import uuid
        OLD_PORT_RANGE = Cluster.PORT_RANGE
        Cluster.PORT_RANGE = (1, 5)

        def add_cluster():
            cluster = Cluster(jobflow_id=str(uuid.uuid1()))
            cluster.save()
            return cluster

        used_ports = []
        port_list = xrange(*Cluster.PORT_RANGE)
        for i in port_list:
            cluster = add_cluster()
            self.assertTrue(cluster.port)
            used_ports.append(cluster.port)
        self.assertItemsEqual(used_ports, port_list)

        # There are not available ports
        self.assertRaises(CloudmlUIValueError, add_cluster)
        Cluster.PORT_RANGE = OLD_PORT_RANGE

    def test_tunnels(self):
        pass


class ClusterResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Clusters API.
    """
    BASE_URL = '/cloudml/instances/clusters/'
    RESOURCE = ClusterResource
    datasets = [ClusterData, ]
    SHOW = 'jobflow_id,master_node_dns'

    def test_list(self):
        from api.base.resources import ValidationError
        self.check_list(show=self.SHOW)

        # Filtering by status
        self.check_list(show=self.SHOW, count=1,
                        data={'status': 'New'})
        self.check_list(show=self.SHOW, count=ACTIVE_CLUSTERS_COUNT,
                        data={'status': 'Active'})

        # Invalid status passed
        url = self._get_url(status='Inv', show=self.SHOW)
        resp = self.client.get(
            url, headers=HTTP_HEADERS)
        self.assertEquals(
            resp.status_code, 400,
            "Resp of %s %s: %s" % (url, resp.status_code, resp.data))

        # Filtering by jobflow_id
        self.check_list(show=self.SHOW, count=0,
                        data={'jobflow_id': 'inv'})
        self.check_list(
            show=self.SHOW, count=1,
            data={'jobflow_id': ClusterData.cluster_01.jobflow_id})

    def test_details(self):
        cluster = Cluster.query.first()
        self.check_details(show=self.SHOW, obj=cluster)

    @patch('api.instances.tasks.run_ssh_tunnel')
    def test_create_tunnel(self, run_ssh_tunnel):
        cluster = Cluster.query.first()
        url = self._get_url(id=cluster.id, action='create_tunnel')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        # FIXME:
        # self.assertTrue(run_ssh_tunnel.called)
        self.assertEquals(cluster.pid, Cluster.PENDING)

    def test_terminate_tunnel(self):
        cluster = Cluster.query.first()
        cluster.pid = 111
        cluster.save()
        url = self._get_url(id=cluster.id, action='terminate_tunnel')
        resp = self.client.put(url, headers=HTTP_HEADERS)
        self.assertEquals(cluster.pid, None)

    @patch('api.amazon_utils.AmazonEMRHelper.terminate_jobflow')
    def test_delete(self, terminate_jobflow):
        cluster = Cluster.query.first()
        self.check_delete(obj=cluster, check_model_deleted=False)
        self.assertTrue(terminate_jobflow.called)
        self.assertEquals(cluster.status, Cluster.STATUS_TERMINATED)

    def test_post_not_allowed(self):
        url = self._get_url()
        resp = self.client.post(
            url, data={'jobflow_id': 1}, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.METHOD_NOT_ALLOWED)
