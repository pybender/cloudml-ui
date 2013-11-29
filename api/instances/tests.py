from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from views import InstanceResource
from models import Instance
from fixtures import InstanceData


class InstancesTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Instances API.
    """
    BASE_URL = '/cloudml/aws_instances/'
    RESOURCE = InstanceResource
    Model = Instance
    datasets = [InstanceData]

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        instance = self.Model.query.filter_by(name='Instance 1')[0]
        resp = self.check_details(
            show='name,ip,is_default,type', obj=instance)
        instance_resp = resp['instance']
        self.assertEqual(instance_resp['name'], instance.name)
        self.assertEqual(instance_resp['type'], instance.type)
        self.assertEqual(instance_resp['ip'], instance.ip)
        self.assertEqual(instance_resp['is_default'], 'False')

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
