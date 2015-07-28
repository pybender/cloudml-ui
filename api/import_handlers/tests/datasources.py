# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..models import PredefinedDataSource, HIDDEN_PASSWORD
from ..fixtures import PredefinedDataSourceData
from ..views import PredefinedDataSourceResource


class PredefinedDataSourceResourceTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the DataSource API methods. """
    datasets = [PredefinedDataSourceData]
    BASE_URL = '/cloudml/datasources/'
    RESOURCE = PredefinedDataSourceResource
    Model = PredefinedDataSource

    # password should be replaced with stars
    HIDDEN_PASSWORD_REGEX = ".*?{0!s}.*?".format(
        HIDDEN_PASSWORD.replace('*', '\\*'))

    def test_list(self):
        datasources = self.check_list(
            show='name,db,can_edit')['predefined_data_sources']
        ds = datasources[0]
        ds_fixture = PredefinedDataSourceData.datasource_01
        self.assertEqual(ds['name'], ds_fixture.name)
        self.assertFalse(ds['can_edit'])
        self.assertRegexpMatches(ds['db']['conn'], self.HIDDEN_PASSWORD_REGEX)

        ds = datasources[1]
        ds_fixture = PredefinedDataSourceData.datasource_02
        self.assertEqual(ds['name'], ds_fixture.name)
        self.assertTrue(ds['can_edit'])
        self.assertEqual(ds_fixture.db, ds['db'])

    def test_details(self):
        obj = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_01.name).one()
        res = self.check_details(show='name,db,can_edit', obj=obj)
        ds = res['predefined_data_source']
        ds_fixture = PredefinedDataSourceData.datasource_01
        self.assertEqual(ds['name'], ds_fixture.name)
        self.assertFalse(ds['can_edit'])
        self.assertRegexpMatches(ds['db']['conn'], self.HIDDEN_PASSWORD_REGEX)

        obj = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_02.name).one()
        res = self.check_details(show='name,db,can_edit', obj=obj)
        ds = res['predefined_data_source']
        ds_fixture = PredefinedDataSourceData.datasource_02
        self.assertEqual(ds['name'], ds_fixture.name)
        self.assertTrue(ds['can_edit'])
        self.assertEqual(ds_fixture.db, ds['db'])

    def test_add(self):
        data = {'type': 'sql',
                'name': 'new',
                'db': 'invalid'}
        self.check_edit_error(
            data, {"db": "JSON file is corrupted. Can not load it: invalid"})

        data['db'] = json.dumps({"a": "1"})
        self.check_edit_error(data, {"db": "vendor is required"})

        db_settings = {'vendor': 'postgres', 'conn': 'conn str'}
        data['db'] = json.dumps(db_settings)
        resp, obj = self.check_edit(data)
        self.assertEqual(obj.name, data['name'])
        self.assertEqual(obj.type, data['type'])
        self.assertEqual(obj.db, db_settings)

    def test_edit(self):
        data = {'name': 'new name'}
        ds = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_01.name).one()
        url = self._get_url(id=ds.id)
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 401)  # haven't permissions

        ds = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_02.name).one()
        self.check_edit(data, id=ds.id)

    def test_delete(self):
        ds = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_01.name).one()
        url = self._get_url(id=ds.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 401)  # haven't permissions

        ds = PredefinedDataSource.query.filter_by(
            name=PredefinedDataSourceData.datasource_02.name).one()
        self.check_delete(obj=ds)
