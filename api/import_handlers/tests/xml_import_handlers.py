import uuid
import json
from datetime import datetime

from mock import patch, MagicMock
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from api.servers.fixtures import ServerData
from api.servers.models import Server
from ..views import XmlImportHandlerResource, XmlEntityResource,\
    XmlDataSourceResource, XmlInputParameterResource, XmlFieldResource,\
    XmlQueryResource, XmlScriptResource, XmlSqoopResource
from ..models import XmlImportHandler, XmlDataSource,\
    XmlScript, XmlField, XmlEntity, XmlInputParameter, XmlQuery, XmlSqoop

from lxml import etree

class XmlImportHandlerTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the XML ImportHandlers API.
    """
    BASE_URL = '/cloudml/xml_import_handlers/'
    RESOURCE = XmlImportHandlerResource
    Model = XmlImportHandler
    datasets = [ServerData]

    def setUp(self):
        super(XmlImportHandlerTests, self).setUp()
        name = str(uuid.uuid1())
        with open('conf/extract.xml', 'r') as fp:
            resp_data = self._check(method='post', data={
                'name': name,
                'data': fp.read()
            })
        self.assertEqual(resp_data[self.RESOURCE.OBJECT_NAME]['name'], name)
        self.obj = self.Model.query.filter_by(name=name).first()

    def test_list(self):
        self.check_list(show='name,import_params')

    def test_details(self):
        resp = self.check_details(show='name,import_params', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['import_params'], self.obj.import_params)

        resp = self.check_details(show='name,xml', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        
        print obj['xml']
        xmlRoot = etree.fromstring(obj['xml'])
        self.assertEqual(xmlRoot.tag, 'plan')
        xmlEntities = xmlRoot.xpath('./import/entity[@datasource="odw"][@name="application"]')
        self.assertEqual(1, len(xmlEntities))
        
        fields = xmlEntities[0].xpath('./entity[@datasource="employer_info"][@name="employer_info"]/\
            field[@name="employer.op_country_tz"]')
        self.assertEqual(1, len(fields))
        self.assertEqual('$.op_country_tz', fields[0].attrib.get('jsonpath'))
        self.assertEqual('string', fields[0].attrib.get('type'))
        self.assertEqual(None, fields[0].attrib.get('multipart'))
        self.assertEqual(None, fields[0].attrib.get('required'))
        
        fields = xmlEntities[0].xpath('./entity[@datasource="employer_info"][@name="employer_info"]/\
            field[@name="employer.op_tot_jobs_filled"]')
        self.assertEqual(1, len(fields))
        self.assertEqual('$.op_tot_jobs_filled', fields[0].attrib.get('jsonpath'))
        self.assertEqual('string', fields[0].attrib.get('type'))
        self.assertEqual('true', fields[0].attrib.get('multipart'))
        self.assertEqual(None, fields[0].attrib.get('required'))
        
        fields = xmlEntities[0].xpath('./entity[@datasource="employer_info"][@name="employer_info"]/\
            field[@name="employer.country"]')
        self.assertEqual(1, len(fields))
        self.assertEqual('$.op_country', fields[0].attrib.get('jsonpath'))
        self.assertEqual('string', fields[0].attrib.get('type'))
        self.assertEqual(None, fields[0].attrib.get('multipart'))
        self.assertEqual('true', fields[0].attrib.get('required'))

        resp = self._check(show='name,entities', id=self.obj.id)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertTrue('fields' in obj['entity'])
        self.assertEqual(3, len(obj['entity']['fields']))
        self.assertEqual(2, len(obj['entity']['entities']))

    def test_edit_name(self):
        data = {"name": "new name"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.name, data['name'])

    def test_delete(self):
        models_to_check = [
            (XmlDataSource, 3, XmlDataSource.query.count()),
            (XmlEntity, 3, XmlEntity.query.count()),
            (XmlInputParameter, 2, XmlInputParameter.query.count()),
            (XmlScript, 1, XmlScript.query.count())
        ]

        for model, count, count_all in models_to_check:
            self.assertEqual(model.query.filter_by(
                import_handler_id=self.obj.id).count(), count)

        self.check_delete()

        for model, count, count_all in models_to_check:
            self.assertEqual(model.query.filter_by(
                import_handler_id=self.obj.id).count(), 0)
            self.assertEqual(model.query.count(), count_all - count)

    @mock_s3
    @patch('api.servers.tasks.upload_import_handler_to_server')
    def test_upload_to_server(self, mock_task):
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        resp = self._check(method='put', action='upload_to_server', data={
            'server': server.id
        })
        self.assertTrue(mock_task.delay.called)
        self.assertTrue('status' in resp)

    def test_put_run_sql_action(self):
        url = self._get_url(id=self.obj.id, action='run_sql')

        # forms validation error
        resp = self.client.put(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue(resp_obj.has_key('response'))
        self.assertTrue(resp_obj['response'].has_key('error'))

        # no parameters
        resp = self.client.put(url,
                               data={'sql': 'SELECT NOW() WHERE #{something}',
                                     'limit': 2,
                                     'datasource': 'odw'},
                               headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue(resp_obj.has_key('response'))
        self.assertTrue(resp_obj['response'].has_key('error'))

        # good
        iter_mock = MagicMock()
        iter_mock.return_value = [{'now': datetime(2014, 7, 21, 15, 52, 5, 308936)}]
        with patch.dict('api.import_handlers.models.import_handlers.CoreImportHandler.DB_ITERS', {'postgres': iter_mock}):
            resp = self.client.put(url,
                                   data={'sql': 'SELECT NOW() WHERE #{something}',
                                         'limit': 2,
                                         'datasource': 'odw',
                                         'params': json.dumps({'something': 'TRUE'})},
                                   headers=HTTP_HEADERS)
            resp_obj = json.loads(resp.data)
            self.assertTrue(resp_obj.has_key('data'))
            self.assertTrue(resp_obj['data'][0].has_key('now'))
            self.assertTrue(resp_obj.has_key('sql'))
            iter_mock.assert_called_with(['SELECT NOW() WHERE TRUE LIMIT 2'],
                                         "host='localhost' dbname='odw' "
                                         "user='postgres' password='postgres'")

class IHLoadMixin(object):
    def load_import_handler(self, filename='conf/extract.xml'):
        name = str(uuid.uuid1())
        with open(filename, 'r') as fp:
            resp_data = self.client.post(
                '/cloudml/xml_import_handlers/',
                data={
                    'name': name,
                    'data': fp.read()
                },
                headers=HTTP_HEADERS)
            resp_data = json.loads(resp_data.data)
        return resp_data[XmlImportHandlerResource.OBJECT_NAME]['id']


class XmlEntityTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Entities API.
    """
    BASE_URL = ''
    RESOURCE = XmlEntityResource
    Model = XmlEntity

    def setUp(self):
        super(XmlEntityTests, self).setUp()
        handler_id = self.load_import_handler()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/entities/'.format(
            handler_id)
        self.obj = XmlEntity.query.filter_by(import_handler_id=handler_id,
                                              name='application').one()

    def test_delete(self):
        field_count = XmlField.query.count()
        entity_count = XmlEntity.query.count()
        query_count = XmlQuery.query.count()

        self.assertEqual(XmlField.query.filter_by(
            entity_id=self.obj.id).count(), 3)
        self.assertEqual(XmlEntity.query.filter_by(
            entity_id=self.obj.id).count(), 2)
        query_id = self.obj.query_obj.id

        self.check_delete()

        self.assertEqual(XmlField.query.filter_by(
            entity_id=self.obj.id).count(), 0)
        self.assertEqual(XmlEntity.query.filter_by(
            entity_id=self.obj.id).count(), 0)
        self.assertEqual(XmlQuery.query.filter_by(id=query_id).count(), 0)

        self.assertEqual(XmlField.query.count(), field_count - 11)
        self.assertEqual(XmlEntity.query.count(), entity_count - 3)
        self.assertEqual(XmlQuery.query.count(), query_count - 1)

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        resp = self.check_details(show='name', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)


class XmlDataSourceTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Datasources API.
    """
    BASE_URL = ''
    RESOURCE = XmlDataSourceResource
    Model = XmlDataSource

    def setUp(self):
        super(XmlDataSourceTests, self).setUp()
        handler_id = self.load_import_handler()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/datasources/'.format(
            handler_id)
        self.obj = XmlDataSource.query.filter_by(import_handler_id=handler_id,
                                                 name='odw').one()

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        resp = self.check_details(show='name', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)


class XmlInputParameterTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML InputParameter API.
    """
    BASE_URL = ''
    RESOURCE = XmlInputParameterResource
    Model = XmlInputParameter

    def setUp(self):
        super(XmlInputParameterTests, self).setUp()
        handler_id = self.load_import_handler()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/input_parameters/'.format(
            handler_id)
        self.obj = XmlInputParameter.query.filter_by(import_handler_id=handler_id,
                                                     name='start').one()

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        resp = self.check_details(show='name', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)

    def test_configuration(self):
        resp = self._check(method='get', action='configuration')
        self.assertTrue('configuration' in resp)
        self.assertTrue('types' in resp['configuration'])


class XmlScriptTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Script API.
    """
    BASE_URL = ''
    RESOURCE = XmlScriptResource
    Model = XmlScript

    def setUp(self):
        super(XmlScriptTests, self).setUp()
        handler_id = self.load_import_handler()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/scripts/'.format(
            handler_id)
        self.obj = XmlScript.query.filter_by(import_handler_id=handler_id).one()

    def test_list(self):
        self.check_list(show='data')

    def test_details(self):
        resp = self.check_details(show='data', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['data'], self.obj.data)


class XmlFieldTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Field API.
    """
    BASE_URL = ''
    RESOURCE = XmlFieldResource
    Model = XmlField

    def setUp(self):
        super(XmlFieldTests, self).setUp()
        handler_id = self.load_import_handler()
        self.entity = XmlEntity.query.filter_by(import_handler_id=handler_id,
                                                name='application').one()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/entities/{1!s}/fields/'.format(
            handler_id, self.entity.id)
        self.obj = XmlField.query.filter_by(entity_id=self.entity.id,
                                            name='application_id').one()

    def test_list(self):
        self.check_list(show='name', query_params={
            'entity_id': self.entity.id
        })

    def test_details(self):
        resp = self.check_details(show='name', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)

    def test_configuration(self):
        resp = self._check(method='get', action='configuration')
        self.assertTrue('configuration' in resp)
        self.assertTrue('types' in resp['configuration'])
        self.assertTrue('transform' in resp['configuration'])
        
    def test_required_mutlipart_serialization(self):
        field = XmlField.query.filter_by(name='employer.op_timezone').one()
        self.assertFalse(field.required)
        self.assertFalse(field.multipart)
        field = XmlField.query.filter_by(name='employer.op_country_tz').one()
        self.assertFalse(field.required)
        self.assertFalse(field.multipart)
        field = XmlField.query.filter_by(name='employer.op_tot_jobs_filled').one()
        self.assertFalse(field.required)
        self.assertTrue(field.multipart)
        field = XmlField.query.filter_by(name='employer.country').one()
        self.assertTrue(field.required)
        self.assertFalse(field.multipart)


class XmlQueryTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Query API.
    """
    BASE_URL = ''
    RESOURCE = XmlQueryResource
    Model = XmlQuery

    def setUp(self):
        super(XmlQueryTests, self).setUp()
        handler_id = self.load_import_handler()
        self.entity = XmlEntity.query.filter_by(import_handler_id=handler_id,
                                                name='application').one()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/entities/{1!s}/queries/'.format(
            handler_id, self.entity.id)
        self.obj = self.entity.query_obj

    def test_list(self):
        self.check_list(show='text')

    def test_details(self):
        resp = self.check_details(show='text', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['text'], self.obj.text)


class XmlSqoopTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Sqoop API.
    """
    BASE_URL = ''
    RESOURCE = XmlSqoopResource
    Model = XmlSqoop

    def setUp(self):
        super(XmlSqoopTests, self).setUp()
        handler_id = self.load_import_handler(
            'api/import_handlers/tests/pig-train-import-handler.xml')
        self.entity = XmlEntity.query.filter_by(import_handler_id=handler_id,
                                                name='application').one()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/entities/{1!s}/sqoop_imports/'.format(
            handler_id, self.entity.id)
        self.obj = self.entity.sqoop_imports[0]

    def test_list(self):
        self.check_list(show='table,datasource,text')

    def test_details(self):
        resp = self.check_details(show='table,datasource,text', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['text'], self.obj.text)
        self.assertEqual(obj['table'], self.obj.table)
        self.assertEqual(obj['datasource']['name'], 'sqoop_db_datasource')
