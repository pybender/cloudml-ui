import uuid
import json

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..views import XmlImportHandlerResource, XmlEntityResource,\
    XmlDataSourceResource, XmlInputParameterResource, XmlFieldResource,\
    XmlQueryResource, XmlScriptResource
from ..models import XmlImportHandler, XmlDataSource,\
    XmlScript, XmlField, XmlEntity, XmlInputParameter, XmlQuery


class XmlImportHandlerTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the XML ImportHandlers API.
    """
    BASE_URL = '/cloudml/xml_import_handlers/'
    RESOURCE = XmlImportHandlerResource
    Model = XmlImportHandler

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
        self.assertTrue('<plan>' in obj['xml'])
        self.assertTrue('<entity datasource="odw" name="application">'
                        in obj['xml'])
        self.assertTrue('<field jsonpath="$.op_country" name="employer.country" type="string"/>'
                        in obj['xml'])

        resp = self.check_details(show='name,entities', obj=self.obj)
        obj = resp[self.RESOURCE.OBJECT_NAME]
        self.assertTrue('fields' in obj['entity'])
        self.assertEqual(2, len(obj['entity']['fields']))
        self.assertEqual(3, len(obj['entity']['entities']))

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


class IHLoadMixin(object):
    def load_import_handler(self):
        name = str(uuid.uuid1())
        with open('conf/extract.xml', 'r') as fp:
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
