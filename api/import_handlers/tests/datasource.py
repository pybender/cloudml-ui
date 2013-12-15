import json

from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from ..models import PredefinedDataSource
from ..fixtures import PredefinedDataSourceData
from ..views import PredefinedDataSourceResource


class PredefinedDataSourceResourceTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the DataSource API methods. """
    datasets = [PredefinedDataSourceData]
    BASE_URL = '/cloudml/datasources/'
    RESOURCE = PredefinedDataSourceResource
    Model = PredefinedDataSource

    def setUp(self):
        super(PredefinedDataSourceResourceTests, self).setUp()
        self.obj = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_01.name).one()
        self.assertTrue(self.obj)

    def test_list(self):
        self.check_list(show='name,db')

    def test_details(self):
        self.check_details(show='name,db')

    def test_add(self):
        data = {'type': 'sql',
                'name': 'new',
                'db': 'invalid'}
        self.check_edit_error(data, {"db": "invalid json: invalid"})

        data['db'] = json.dumps({"a": "1"})
        self.check_edit_error(data, {"db": "vendor is required"})

        db_settings = {'vendor': 'postgres', 'conn': 'conn str'}
        data['db'] = json.dumps(db_settings)
        resp, obj = self.check_edit(data)
        self.assertEqual(obj.name, data['name'])
        self.assertEqual(obj.type, data['type'])
        self.assertEqual(obj.db, db_settings)

    # TODO:
    def test_edit(self):
        pass

    def test_delete(self):
        pass
