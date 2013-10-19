from bson import ObjectId

from utils import BaseTestCase
from api.views import DataSourceResource


class DataSourceTests(BaseTestCase):
    """
    Tests of the DataSource API methods.
    """
    ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('datasources.json', )
    BASE_URL = '/cloudml/datasources/'
    RESOURCE = DataSourceResource

    def setUp(self):
        super(DataSourceTests, self).setUp()
        self.Model = self.db.DataSource
        self.obj = self.Model.get_from_id(ObjectId(self.ID))
        self.assertTrue(self.obj)

    def test_strange_behaviour(self):
        # TODO: check why db_settings field always presents in DataSource model
        one = self.Model.find_one({}, ['name'])
        #self.assertEqual(one.keys(), [u'_id', u'name', 'db_settings'])

    def test_list(self):
        self._check_list(show='name,db_settings')

    def test_details(self):
        self._check_details(show='name,db_settings')

    def test_post(self):
        post_data = {'type': 'sql',
                     'name': 'new'}
        resp, obj = self._check_post(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.type, post_data['type'])
