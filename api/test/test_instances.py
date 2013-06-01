from utils import BaseTestCase
from api.views import InstanceResource


class InstancesTests(BaseTestCase):
    """
    Tests of the Instances API.
    """
    INSTANCE_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('instances.json', )
    BASE_URL = '/cloudml/aws_instances/'
    RESOURCE = InstanceResource

    def setUp(self):
        super(InstancesTests, self).setUp()
        self.Model = self.db.Instance
        self.obj = self.Model.find_one({'name': 'Instance 1'})
        self.assertTrue(self.obj)

    def test_list(self):
        self._check_list()

    def test_details(self):
        self._check_details()

    def test_post(self):
        post_data = {'ip': '1.1.1.1',
                     'type': 'small',
                     'name': 'new'}
        resp, obj = self._check_post(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.ip, post_data['ip'])
        self.assertEqual(obj.type, post_data['type'])
