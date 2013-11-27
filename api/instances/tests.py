from api.base.test_utils import BaseTestCase, TestChecksMixin
from views import InstanceResource
from models import Instance


class InstancesTests(BaseTestCase, TestChecksMixin):
    """
    Tests of the Instances API.
    """
    INSTANCE_ID = '5170dd3a106a6c1631000000'

    FIXTURES = ('instances.json', )
    BASE_URL = '/cloudml/aws_instances/'
    RESOURCE = InstanceResource
    Model = Instance

    def setUp(self):
        super(InstancesTests, self).setUp()
        self.obj = self.Model.query.filter_by(name='Instance 1').one()
        self.assertTrue(self.obj)

    def test_list(self):
        self.check_list(show='name')

    # def test_details(self):
    #     self._check_details()

    # def test_post(self):
    #     post_data = {'ip': '1.1.1.1',
    #                  'type': 'small',
    #                  'name': 'new'}
    #     resp, obj = self._check_post(post_data, load_model=True)
    #     self.assertEqual(obj.name, post_data['name'])
    #     self.assertEqual(obj.ip, post_data['ip'])
    #     self.assertEqual(obj.type, post_data['type'])

    # def test_edit_is_default(self):
    #     url = self._get_url(id=self.obj._id)
    #     self.assertFalse(self.obj.is_default)
    #     data = {'is_default': 'true'}
    #     resp = self.app.put(url, data=data, headers=HTTP_HEADERS)
    #     self.assertEquals(resp.status_code, httplib.OK)
    #     data = json.loads(resp.data)
    #     self.assertTrue(self.RESOURCE.OBJECT_NAME in data)
    #     self.obj.reload()
    #     self.assertTrue(self.obj.is_default)
