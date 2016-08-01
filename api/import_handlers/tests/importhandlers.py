import uuid
import json
import os
from datetime import datetime

from mock import patch, MagicMock, ANY
from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from api.servers.fixtures import ServerData
from api.servers.models import Server
from ..views import XmlImportHandlerResource, XmlEntityResource, \
    XmlDataSourceResource, XmlInputParameterResource, XmlFieldResource, \
    XmlQueryResource, XmlScriptResource, XmlSqoopResource, \
    PredictModelResource, PredictModelWeightResource
from ..models import XmlImportHandler, XmlDataSource, db, \
    XmlScript, XmlField, XmlEntity, XmlInputParameter, XmlQuery, XmlSqoop, \
    PredictModel, PredictModelWeight
from ..fixtures import *

from lxml import etree

APP_URL = '/cloudml/xml_import_handlers/'


class XmlImportHandlerModelTests(BaseDbTestCase):
    datasets = IMPORT_HANDLER_FIXTURES

    def setUp(self):
        super(XmlImportHandlerModelTests, self).setUp()
        self.handler = XmlImportHandler.query.filter_by(
            name="Xml Handler 1").one()

    def test_get_plan_config(self):
        self.assertEquals(
            IMPORTHANDLER_FROM_FIXTURES, self.handler.get_plan_config())
        self.assertEquals(
            IMPORTHANDLER_FROM_FIXTURES, self.handler.data)

    def test_load_import_handler(self):
        handler = XmlImportHandler(name='My import handler')
        handler.save()
        handler.data = IMPORTHANDLER

        self.assertEquals(len(handler.xml_input_parameters), 2)
        self.assertEquals(len(handler.xml_scripts), 1)

        # 3 ds defined in the file + one extra input datasource
        self.assertEquals(
            len(handler.xml_data_sources), 4, handler.xml_data_sources)
        self.assertItemsEqual(
            handler.get_fields(),
            ['application_id',
             'employer.op_timezone',
             'employer.op_country_tz',
             'employer.op_tot_jobs_filled',
             'employer.country',
             'contractor.dev_is_looking',
             'contractor.dev_is_looking_week',
             'contractor.dev_active_interviews',
             'contractor.dev_availability'])

    def test_get_fields(self):
        self.assertEqual(
            self.handler.get_fields(), ['opening_id', 'hire_outcome'])

    def test_list_fields(self):
        fields = self.handler.list_fields()
        self.assertEqual(2, len(fields))
        self.assertEqual('opening_id', fields[0].name)
        self.assertEqual('integer', fields[0].type)

        self.assertEqual('hire_outcome', fields[1].name)
        self.assertEqual('string', fields[1].type)

        # another handler
        handler = XmlImportHandler(name='xml ih')
        handler.data = IMPORTHANDLER
        handler.save()
        fields = handler.list_fields()
        self.assertEqual(11, len(fields))
        self.assertEqual(sorted([f.name for f in fields]),
                         sorted([
                             'application_id',
                             'employer_info',
                             'contractor_info',
                             'employer.op_timezone',
                             'employer.op_country_tz',
                             'employer.op_tot_jobs_filled',
                             'employer.country',
                             'contractor.dev_is_looking',
                             'contractor.dev_is_looking_week',
                             'contractor.dev_active_interviews',
                             'contractor.dev_availability']))

    def test_get_ds_details_for_query(self):
        vendor, conn = self.handler._get_ds_details_for_query('ds')
        self.assertEqual(vendor, 'postgres')
        self.assertEqual(conn, "host='localhost' dbname='odw' \
user='postgres' password='postgres'")

    def test_update_import_params(self):
        param = XmlInputParameter(
            name='param', type='string', import_handler=self.handler)
        param.save()
        db.session.refresh(self.handler)
        self.assertItemsEqual(
            self.handler.import_params,
            ['start', 'end', 'param'])

        param.delete()
        db.session.refresh(self.handler)
        self.assertItemsEqual(
            self.handler.import_params, ['start', 'end'])


class XmlImportHandlerTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the XML ImportHandlers API.
    """
    BASE_URL = APP_URL
    RESOURCE = XmlImportHandlerResource
    Model = XmlImportHandler
    datasets = [ServerData]

    def setUp(self):
        super(XmlImportHandlerTests, self).setUp()
        self.obj = get_importhandler('importhandler.xml')

    def test_list(self):
        self.check_list(show='name,import_params')

    def test_details(self):
        resp = self.check_details(show='name,import_params', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['name'], self.obj.name)
        self.assertEqual(obj['import_params'], self.obj.import_params)

        resp = self.check_details(show='name,xml', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]

        xmlRoot = etree.fromstring(obj['xml'])
        self.assertEqual(xmlRoot.tag, 'plan')
        xmlEntities = xmlRoot.xpath(
            './import/entity[@datasource="odw"][@name="application"]')
        self.assertEqual(1, len(xmlEntities))

        fields = xmlEntities[0].xpath(
            './entity[@datasource="employer_info"][@name="employer_info"]/\
            field[@name="employer.op_country_tz"]')
        self.assertEqual(1, len(fields))
        self.assertEqual('$.op_country_tz', fields[0].attrib.get('jsonpath'))
        self.assertEqual('string', fields[0].attrib.get('type'))
        self.assertEqual(None, fields[0].attrib.get('multipart'))
        self.assertEqual(None, fields[0].attrib.get('required'))

        fields = xmlEntities[0].xpath(
            './entity[@datasource="employer_info"][@name="employer_info"]/\
            field[@name="employer.op_tot_jobs_filled"]')
        self.assertEqual(1, len(fields))
        self.assertEqual(
            '$.op_tot_jobs_filled', fields[0].attrib.get('jsonpath'))
        self.assertEqual('string', fields[0].attrib.get('type'))
        self.assertEqual('true', fields[0].attrib.get('multipart'))
        self.assertEqual(None, fields[0].attrib.get('required'))

        fields = xmlEntities[0].xpath(
            './entity[@datasource="employer_info"][@name="employer_info"]/\
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

    def test_datasource_credentials(self):
        def _check(hide=False):
            resp = self.check_details(
                show='xml,xml_data_sources', obj=self.obj)
            obj = resp[self.RESOURCE.OBJECT_NAME]
            self.assertTrue(len(obj['xml_data_sources']))
            for ds in obj['xml_data_sources']:
                if hide:
                    self.assertFalse(ds['params'])
                else:
                    self.assertNotEquals(ds['params'], None)
            xmlRoot = etree.fromstring(obj['xml'])
            datasources = xmlRoot.xpath('./datasources/*')
            self.assertTrue(datasources)
            ds = datasources[0]
            self.assertEquals(ds.tag, "db")
            if hide:
                self.assertFalse(ds.get('vendor'))
            else:
                self.assertTrue(ds.get('vendor'))

        self.obj.created_by_id = 2
        self.obj.save()
        _check(hide=False)

        self.obj.created_by_id = 1
        self.obj.save()
        _check(hide=True)

    def test_edit_name(self):
        data = {"name": "new name"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.name, data['name'])

    def test_edit_deployed(self):
        # check handler uploaded to server
        self.obj.locked = True
        self.obj.save()
        data = {"name": "new"}
        url = self._get_url(id=self.obj.id)
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('has been deployed', resp.data)

    def test_upload_obsolete_import_handler(self):
        name = str(uuid.uuid1())
        # Obsolete import handler uploading
        # Check comportability
        resp_data = self._check(method='post', data={
            'name': name,
            'data': EXTRACT_OBSOLETE
        })
        handler = self.Model.query.filter_by(name=name).first()

        ent = XmlEntity.query.filter_by(
            import_handler=handler, name='application').one()
        joined = XmlField.query.filter_by(
            entity=ent, name='joined_field').one()
        delimited = XmlField.query.filter_by(
            entity=ent, name='delimited_field').one()
        self.assertEquals(joined.delimiter, ";")
        self.assertEquals(delimited.delimiter, ";")

    def test_delete(self):
        models_to_check = [
            (XmlDataSource, 4, XmlDataSource.query.count()),
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

    @patch('api.servers.tasks.upload_import_handler_to_server.s')
    @patch('api.servers.tasks.update_at_server.s')
    def test_upload_to_server(self, update_task, mock_task):
        server = Server.query.filter_by(name=ServerData.server_01.name).one()
        resp = self._check(method='put', action='upload_to_server', data={
            'server': server.id
        })
        mock_task.return_value = 'importhandlers/xyz.xml'
        self.assertTrue(mock_task.called)
        self.assertTrue(update_task.called)
        self.assertTrue('status' in resp)

    def test_put_run_sql_action(self):
        url = self._get_url(id=self.obj.id, action='run_sql')

        # forms validation error
        resp = self.client.put(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue('response' in resp_obj)
        self.assertTrue('error' in resp_obj['response'])

        # no parameters
        resp = self.client.put(url,
                               data={'sql': 'SELECT NOW() WHERE #{something}',
                                     'limit': 2,
                                     'datasource': 'odw'},
                               headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue('response' in resp_obj)
        self.assertTrue('error' in resp_obj['response'])

        # good
        iter_mock = MagicMock()
        iter_mock.return_value = [
            {'now': datetime(2014, 7, 21, 15, 52, 5, 308936)}]
        with patch.dict('cloudml.importhandler.datasources.DbDataSource.DB',
                        {'postgres': [iter_mock, iter_mock]}):
            resp = self.client.put(
                url,
                data={'sql': 'SELECT NOW() WHERE #{something}',
                      'limit': 2,
                      'datasource': 'odw',
                      'params': json.dumps({'something': 'TRUE'})},
                headers=HTTP_HEADERS)
            resp_obj = json.loads(resp.data)
            self.assertTrue('data' in resp_obj)
            self.assertTrue('now' in resp_obj['data'][0])
            self.assertTrue('sql' in resp_obj)
            iter_mock.assert_called_with(['SELECT NOW() WHERE TRUE LIMIT 2'],
                                         "host='localhost' dbname='odw' "
                                         "user='postgres' password='postgres'")

    def test_get_list_fields(self):
        url = self._get_url(id=self.obj.id, action='list_fields')

        resp = self.client.get(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue('xml_fields' in resp_obj)
        self.assertEqual(
            11, len(resp_obj['xml_fields']),
            "Actual fields are: {0}".format(
                [item['name'] for item in resp_obj['xml_fields']]))

    def test_put_upload_to_server_action(self):
        url = self._get_url(id=self.obj.id, action='update_xml')

        # forms validation error, no data
        resp = self.client.put(url, data={}, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)

        # forms validation error, bad xml data
        resp = self.client.put(
            url, data={'data': 'bad xml'}, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn('Valid XML is expected', resp.data)

        handler = self.obj
        self.assertEqual(
            4, XmlDataSource.query.filter_by(import_handler=handler).count())
        self.assertEqual(
            2,
            XmlInputParameter.query.filter_by(import_handler=handler).count())
        self.assertEqual(
            1, XmlScript.query.filter_by(import_handler=handler).count())

        resp = self.client.put(url, data={'data': IMPORTHANDLER},
                               headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertEqual(200, resp.status_code)

        self.assertEqual(
            4, XmlDataSource.query.filter_by(import_handler=handler).count())
        self.assertEqual(
            2,
            XmlInputParameter.query.filter_by(import_handler=handler).count())
        self.assertEqual(
            1, XmlScript.query.filter_by(import_handler=handler).count())

        # incorrect script path in scripts src
        resp = self.client.put(
            url, data={'data': IH_INCORRECT_SCRIPT}, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn('not found', resp.data)

        # invalid python in existing script
        resp = self.client.put(
            url, data={'data': IH_INVALID_PYTHON}, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn('Exception occurs while adding python script', resp.data)

        # 2 scripts (src and text)
        resp = self.client.put(url, data={'data': EXTRACT_OBSOLETE},
                               headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            2, XmlScript.query.filter_by(import_handler=handler).count())

    def test_get_xml_download_action(self):
        url = self._get_url(id=self.obj.id, action='xml_download')
        resp = self.client.get(url, headers=HTTP_HEADERS)

        self.assertTrue('<plan>' in resp.data)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.mimetype, 'text/xml')
        self.assertEquals(
            resp.headers['Content-Disposition'],
            'attachment; filename="%s-importhandler.xml"' % (self.obj.name, ))


class IHLoadMixin(object):
    pass


class XmlEntityTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Entities API.
    """
    BASE_URL = ''
    RESOURCE = XmlEntityResource
    Model = XmlEntity
    datasets = [XmlDataSourceData]

    def setUp(self):
        super(XmlEntityTests, self).setUp()
        self.handler = get_importhandler('importhandler.xml')
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/entities/'.format(
            self.handler.id)
        self.obj = XmlEntity.query.filter_by(
            import_handler_id=self.handler.id,
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

    def test_edit_ih_part(self):
        entity = XmlEntity.query.filter_by(
            name=XmlEntityData.xml_entity_01.name).one()
        ds = XmlDataSource.query.filter_by(
            name=XmlDataSourceData.datasource_01.name).one()
        # Import handler is created by another user
        user = User.query.filter_by(name=UserData.user_01.name).first()
        self.handler.created_by_id = user.id
        self.handler.save()

        # put
        url = self._get_url(id=self.obj.id)
        resp = self.client.put(url, data={"name": "nn"}, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn("Item is created by another user.", resp.data)

        # post
        resp = self.client.post(self.BASE_URL,
                                data={"name": "nn",
                                      "import_handler_id": self.handler.id,
                                      "entity_id": entity.id,
                                      "datasource": ds.id},
                                headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn("Forbidden to add entities to this import handler",
                      resp.data)

        # delete
        url = self._get_url(id=self.obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn("Forbidden to delete entities of this import handler. "
                      "Item is created by another user.", resp.data)

        # Import handler is created by the same user
        user = User.query.filter_by(name=UserData.user_02.name).first()
        self.handler.created_by_id = user.id
        self.handler.save()
        # post
        resp = self.client.post(self.BASE_URL,
                                data={"name": "nn",
                                      "import_handler_id": self.handler.id,
                                      "entity_id": entity.id,
                                      "datasource": ds.id},
                                headers=HTTP_HEADERS)
        self.assertEqual(201, resp.status_code)
        resp = json.loads(resp.data)
        obj = XmlEntity.query.get(resp[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.name, "nn")

        # put
        url = self._get_url(id=self.obj.id)
        resp = self.client.put(url, data={"name": "nn"}, headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        resp = json.loads(resp.data)
        obj = XmlEntity.query.get(resp[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.name, "nn")

        # delete
        url = self._get_url(id=self.obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(204, resp.status_code)


class XmlDataSourceTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Datasources API.
    """
    BASE_URL = ''
    RESOURCE = XmlDataSourceResource
    Model = XmlDataSource

    def setUp(self):
        super(XmlDataSourceTests, self).setUp()
        self.handler = get_importhandler()
        self.BASE_URL = '{0!s}{1!s}/datasources/'.format(
            APP_URL, self.handler.id)
        self.obj = XmlDataSource.query.filter_by(
            import_handler_id=self.handler.id,
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
        self.handler = get_importhandler()
        self.BASE_URL = '{0!s}{1!s}/input_parameters/'.format(
            APP_URL, self.handler.id)
        self.obj = XmlInputParameter.query.filter_by(
            import_handler_id=self.handler.id,
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
        self.handler = get_importhandler()
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/scripts/'.format(
            self.handler.id)
        self.obj = XmlScript.query.filter_by(
            import_handler_id=self.handler.id).one()

    def test_list(self):
        self.check_list(show='data')

    def test_details(self):
        resp = self.check_details(show='data', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['data'], self.obj.data)

    @patch('api.amazon_utils.AmazonS3Helper.save_key_string')
    @patch('cloudml.importhandler.scripts.Script._process_amazon_file')
    def test_post_put(self, process_mock, save_mock):
        handler = get_importhandler(filename='obsolete_extract.xml')
        self.handler_amazon = handler
        url = '/cloudml/xml_import_handlers/{0!s}/scripts/'.format(handler.id)
        data_01 = {'data_file': '2+2', 'import_handler_id': handler.id}
        data_02 = {'data_file': 'kwwkk', 'import_handler_id': handler.id}
        data_03 = {'data': '2*11', 'data_file': '3*11',
                   'data_url': './api/import_handlers/fixtures/functions.py',
                   'import_handler_id': handler.id}
        data_04 = {'data': '2*11', 'import_handler_id': handler.id}
        data_05 = {'data': '2*12', 'import_handler_id': handler.id}
        data_06 = {'data_url': './api/import_handlers/fixtures/functions.py',
                   'import_handler_id': handler.id, 'data': '2+3'}
        data_07 = {'data_url': './api/import_handlers/fixtures/function.py',
                   'import_handler_id': handler.id}
        data_08 = {'data_url':
                   './api/import_handlers/fixtures/bad_functions.py',
                   'import_handler_id': handler.id}
        data_09 = {'data_url': './api/import_handlers/fixtures/functions.py',
                   'import_handler_id': handler.id,
                   'type': XmlScript.TYPE_PYTHON_CODE}
        data_10 = {'data': '1+1',
                   'import_handler_id': handler.id,
                   'type': XmlScript.TYPE_PYTHON_FILE}

        # correct data file
        resp = self.client.post(url, data=data_01, headers=HTTP_HEADERS)
        self.assertEqual(201, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_FILE)
        key = "{0}_python_script_".format(handler.name)
        self.assertIn(key, obj.data)

        # incorrect data file
        resp = self.client.post(url, data=data_02, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn("Exception occurs while adding python script", resp.data)

        # choose data file
        resp = self.client.post(url, data=data_03, headers=HTTP_HEADERS)
        self.assertEqual(201, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_FILE)
        key = "{0}_python_script_".format(handler.name)
        self.assertIn(key, obj.data)
        amazon_file = obj.data

        # choose data url
        resp = self.client.post(url, data=data_06, headers=HTTP_HEADERS)
        self.assertEqual(201, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_FILE)
        self.assertEqual('./api/import_handlers/fixtures/functions.py',
                         obj.data)

        # incorrect data url (file doesn't exist)
        process_mock.side_effect = Exception('Not found on Amazon')
        resp = self.client.post(url, data=data_07, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn("not found", resp.data)

        # incorrect data in url
        resp = self.client.post(url, data=data_08, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn("Exception occurs while adding python script", resp.data)

        # just correct data
        resp = self.client.post(url, data=data_04, headers=HTTP_HEADERS)
        self.assertEqual(201, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_CODE)
        self.assertEqual(obj.data, '2*11')

        # PUT correct data
        resp = self.client.put(
            '{0}{1}/'.format(url,
                             resp_obj[self.RESOURCE.OBJECT_NAME]['id']),
            data=data_05,
            headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_CODE)
        self.assertEqual(obj.data, '2*12')

        # PUT correct data and data url to amazon (choose data url)
        data_05['data_url'] = amazon_file
        process_mock.return_value = '3*11'
        process_mock.side_effect = None
        resp = self.client.put(
            '{0}{1}/'.format(url,
                             resp_obj[self.RESOURCE.OBJECT_NAME]['id']),
            data=data_05,
            headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_FILE)
        self.assertEqual(obj.data, amazon_file)

        # PUT correct data to previously stored url, it should change type
        data_05['data_url'] = ''
        resp = self.client.put(
            '{0}{1}/'.format(url,
                             resp_obj[self.RESOURCE.OBJECT_NAME]['id']),
            data=data_05,
            headers=HTTP_HEADERS)
        self.assertEqual(200, resp.status_code)
        resp_obj = json.loads(resp.data)
        obj = XmlScript.query.get(resp_obj[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEqual(obj.type, XmlScript.TYPE_PYTHON_CODE)
        self.assertEqual(obj.data, "2*12")

        # type and data mismatch
        resp = self.client.post(url, data=data_09, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn("Code is required for type 'python_code'", resp.data)

        # type and data mismatch
        resp = self.client.post(url, data=data_10, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn("File upload or URL required for type 'python_file'",
                      resp.data)

    def test_get_script_string(self):
        handler = get_importhandler(filename='obsolete_extract.xml')
        script = XmlScript.query.filter_by(import_handler_id=handler.id).all()
        url = '/cloudml/xml_import_handlers/{0}/scripts/{1}/action/' \
              'script_string/'.format(handler.id, script[0].id)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertIn('multiply(x, y)', resp_obj['script_string'])
        self.assertEqual(200, resp.status_code)

        url = '/cloudml/xml_import_handlers/{0}/scripts/{1}/action/' \
              'script_string/'.format(handler.id, script[1].id)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertIn('1+1', resp_obj['script_string'])
        self.assertEqual(200, resp.status_code)


class XmlFieldTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the XML Field API.
    """
    BASE_URL = ''
    RESOURCE = XmlFieldResource
    Model = XmlField

    def setUp(self):
        super(XmlFieldTests, self).setUp()
        self.handler = get_importhandler('importhandler.xml')
        self.entity = XmlEntity.query.filter_by(
            import_handler_id=self.handler.id,
            name='application').one()
        self.BASE_URL = '{0!s}{1!s}/entities/{2!s}/fields/'.format(
            APP_URL, self.handler.id, self.entity.id)
        self.obj = XmlField.query.filter_by(
            entity_id=self.entity.id,
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
        field = XmlField.query.filter_by(
            name='employer.op_timezone').one()
        self.assertFalse(field.required)
        self.assertFalse(field.multipart)
        field = XmlField.query.filter_by(
            name='employer.op_country_tz').one()
        self.assertFalse(field.required)
        self.assertFalse(field.multipart)
        field = XmlField.query.filter_by(
            name='employer.op_tot_jobs_filled').one()
        self.assertFalse(field.required)
        self.assertTrue(field.multipart)
        field = XmlField.query.filter_by(
            name='employer.country').one()
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
        self.handler = get_importhandler()
        self.entity = XmlEntity.query.filter_by(
            import_handler_id=self.handler.id,
            name='application').one()
        self.BASE_URL = '{0!s}{1!s}/entities/{2!s}/queries/'.format(
            APP_URL, self.handler.id, self.entity.id)
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
        self.handler = get_importhandler('pig-train-import-handler.xml')
        self.entity = XmlEntity.query.filter_by(
            import_handler_id=self.handler.id,
            name='application').one()
        self.BASE_URL = '{0!s}{1!s}/entities/{2!s}/sqoop_imports/'.format(
            APP_URL, self.handler.id, self.entity.id)
        self.obj = self.entity.sqoop_imports[0]

    def test_list(self):
        self.check_list(show='table,datasource,text')

    def test_details(self):
        resp = self.check_details(show='table,datasource,text', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertEqual(obj['text'], self.obj.text)
        self.assertEqual(obj['table'], self.obj.table)
        self.assertEqual(obj['datasource']['name'], 'sqoop_db_datasource')

    @patch('cloudml.importhandler.datasources.DbDataSource._get_iter')
    def test_get_pig_fields(self, get_iter_mock):
        get_iter_mock.return_value = [
            ['application', 'bigint', None, 'YES', None],
            ['opening', 'bigint', None, 'YES', None],
            ['employer_info', 'text', None, 'YES', None],
            ['hire_outcome', 'text', None, 'YES', None]]
        sqoop = self.obj
        resp = self._check(action='pig_fields', obj=sqoop, method='put')
        self.assertTrue(get_iter_mock.called)
        print resp
        self.assertItemsEqual('Generating pig fields delayed (link will '
                              'appear in sqoop section)', resp['result'])
        # self.assertItemsEqual(
        #     ['application', 'opening', 'employer_info', 'hire_outcome'],
        #     [fld['column_name'] for fld in resp['fields']]
        # )
#         self.assertTrue("""application:long
# , opening:long
# , employer_info:chararray
# , hire_outcome:chararray""" in resp['sample'])


class PredictModelTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the models in predict section of the xml import handlers.
    """
    BASE_URL = ''
    RESOURCE = PredictModelResource
    Model = PredictModel

    def setUp(self):
        super(PredictModelTests, self).setUp()
        self.handler = get_importhandler('importhandler.xml')
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/\
predict_models/'.format(self.handler.id)
        self.obj = self.handler.predict.models[0]
        self.assertNotEquals(
            self.obj, None, "There is a problem with loading "
            "import handler: no predict models added")

    def test_predict_models_loaded_from_xml(self):
        model = self.handler.predict.models[0]
        self.assertEquals(model.name, 'autohide')
        self.assertEquals(model.value, 'BestMatch.v31')
        self.assertFalse(model.script)
        weights = model.predict_model_weights
        self.assertEquals(len(weights), 2)
        weight = weights[0]
        self.assertEquals(weight.value, '1.23543')
        self.assertTrue(weight.label)
        self.assertFalse(weight.script)

    def test_list(self):
        resp = self.check_list(
            show='id,name,script,value',
            count=1)
        model = resp['predict_models'][0]
        db_model = self.handler.predict.models[0]
        self.assertEquals(model['name'], db_model.name)
        self.assertEquals(model['value'], db_model.value)
        self.assertEquals(model['script'], db_model.script)

    def test_list_invalid_handler(self):
        import sys
        url = '/cloudml/xml_import_handlers/{0!s}/\
predict_models/'.format(sys.maxint)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 401)

    def test_post(self):
        data, model = self.check_edit(
            {'name': 'new name',
             'value': 'val'},
            load_json=True)
        self.assertEquals(model.name, 'new name')

    def test_put(self):
        data, model = self.check_edit(
            {'name': 'new name'},
            id=self.obj.id)
        self.assertEquals(model.name, 'new name')

        data, model = self.check_edit(
            {'script': '1000'},
            id=self.obj.id)
        self.assertEquals(model.script, '1000')

        data, model = self.check_edit(
            {'value': 'value'},
            id=self.obj.id)
        self.assertEquals(model.value, 'value')

        data, model = self.check_edit(
            {'script': ''},
            id=self.obj.id)
        self.assertEquals(model.script, '')


class PredictModelWeightTests(BaseDbTestCase, TestChecksMixin, IHLoadMixin):
    """
    Tests of the models in predict model's weights
    section of the xml import handlers.
    """
    BASE_URL = ''
    RESOURCE = PredictModelWeightResource
    Model = PredictModelWeight

    def setUp(self):
        super(PredictModelWeightTests, self).setUp()
        # Trying to load the import handler with predict models twice.
        self.handler = get_importhandler('importhandler.xml')
        self.handler = XmlImportHandler.query.get(self.handler.id)
        self.predict_model = self.handler.predict.models[0]
        self.obj = self.predict_model.predict_model_weights[0]
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/\
predict_models/{1}/weights/'.format(self.handler.id, self.predict_model.id)

    def test_list(self):
        resp = self.check_list(
            show='id,label,script,value',
            count=2)
        model = resp['predict_model_weights'][0]
        db_weight = self.predict_model.predict_model_weights[0]
        self.assertEquals(model['label'], db_weight.label)
        self.assertEquals(model['value'], db_weight.value)
        self.assertEquals(model['script'], db_weight.script)

    def test_details(self):
        self.check_details(show='label,value')

    def test_post(self):
        post_data = {'label': 'the label',
                     'value': '2',
                     'predict_model_id': self.predict_model.id}
        resp, obj = self.check_edit(post_data, load_model=True)
        self.assertEqual(obj.label, post_data['label'])
        self.assertEqual(obj.predict_model_id, self.predict_model.id)
        self.assertEquals(len(obj.predict_model.predict_model_weights), 3)

    def test_edit(self):
        data = {"label": "new label"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.label, data['label'])

        data = {"value": "new value"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.value, data['value'])

        data = {"script": "new script"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.script, data['script'])

    def test_delete(self):
        self.check_delete()
