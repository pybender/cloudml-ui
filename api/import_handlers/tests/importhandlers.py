import uuid
import json
import os
from datetime import datetime

from mock import patch, MagicMock
from moto import mock_s3

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
        with patch.dict('cloudml.importhandler.datasources.DbDataSource.DB', {'postgres': iter_mock}):
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
        self.assertIn('bad xml', resp.data)

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


class IHLoadMixin(object):
    PIG_IMPORT_HANDLER = os.path.join(
        DIR, '../fixtures/pig-train-import-handler.xml')

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
        self.assertItemsEqual(
            'Generating pig fields delayed (link will appear in sqoop section)',
            resp['result'])
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
        self.assertEquals(model.positive_label_value, 'false')
        self.assertFalse(model.positive_label_script)
        weights = model.predict_model_weights
        self.assertEquals(len(weights), 2)
        weight = weights[0]
        self.assertEquals(weight.value, '1.23543')
        self.assertTrue(weight.label)
        self.assertFalse(weight.script)

    def test_list(self):
        resp = self.check_list(
            show='id,name,script,value,positive_label_value',
            count=1)
        model = resp['predict_models'][0]
        db_model = self.handler.predict.models[0]
        self.assertEquals(model['name'], db_model.name)
        self.assertEquals(model['value'], db_model.value)
        self.assertEquals(model['script'], db_model.script)
        self.assertEquals(
            model['positive_label_value'], db_model.positive_label_value)

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
        print self.obj.id
        data, model = self.check_edit(
            {'name': 'new name'},
            load_json=True,
            id=self.obj.id)
        self.assertEquals(model.name, 'new name')
        # print self.Model.query.get(self.obj.id).name
        # raise


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
