import uuid
import json

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..views import XmlImportHandlerResource, XmlEntityResource
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

    def test_edit_name(self):
        data = {"name": "new name"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.name, data['name'])

    def test_delete(self):
        def _check_models(models_to_check):
            for model, count in models_to_check:
                self.assertEqual(model.query.filter_by(
                    import_handler_id=self.obj.id).count(), count)

        _check_models([(XmlDataSource, 3), (XmlEntity, 3),
                       (XmlInputParameter, 2), (XmlScript, 1)])

        self.check_delete()

        _check_models([(XmlDataSource, 0), (XmlEntity, 0),
                       (XmlInputParameter, 0), (XmlScript, 0)])


class XmlEntityTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the XML Entities API.
    """
    BASE_URL = '/cloudml/xml_import_handlers/'
    RESOURCE = XmlEntityResource
    Model = XmlEntity

    def setUp(self):
        super(XmlEntityTests, self).setUp()
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
        handler_id = resp_data[XmlImportHandlerResource.OBJECT_NAME]['id']
        self.BASE_URL = '/cloudml/xml_import_handlers/{0!s}/entities/'.format(
            handler_id)
        self.obj = self.Model.query.filter_by(import_handler_id=handler_id,
                                              name='application').one()

    def test_delete(self):
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
