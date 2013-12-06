import httplib
import json
from mock import patch
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import ModelResource
from models import Model
from fixtures import ModelData
from api.import_handlers.fixtures import ImportHandlerData, DataSetData
from api.import_handlers.models import DataSet, ImportHandler


class ModelsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Model API.
    """
    BASE_URL = '/cloudml/models/'
    RESOURCE = ModelResource
    Model = Model
    datasets = [ImportHandlerData, DataSetData, ModelData]

    def setUp(self):
        super(ModelsTests, self).setUp()
        self.obj = Model.query.filter_by(
            name=ModelData.model_01.name).one()

    def test_list(self):
        self.check_list(show='')
        self.check_list(show='created_on,updated_on')

    def test_filter(self):
        self.check_list(data={'status': 'New'}, query_params={'status': 'New'})
        # No name filter - all models should be returned
        self.check_list(data={'name': 'Test'}, query_params={})

        # Comparable filter
        self.check_list(data={'comparable': '1'}, query_params={'comparable': True})
        self.check_list(data={'comparable': '0'}, query_params={'comparable': False})

    def test_details(self):
        self.check_details(show='')
        self.check_details(show='created_on,labels')

    def test_datasets(self):
        self.obj.datasets = [
            DataSet.query.filter_by(name=DataSetData.dataset_01.name).first(),
            DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()
        ]
        self.obj.save()
        resp = self.check_details(show='name,datasets')
        self.assertEquals(len(resp[self.RESOURCE.OBJECT_NAME]['datasets']), 2)

    def test_data_fields(self):
        self.obj.datasets = [
            DataSet.query.filter_by(name=DataSetData.dataset_01.name).first(),
            DataSet.query.filter_by(name=DataSetData.dataset_02.name).first()
        ]
        self.obj.save()
        resp = self.check_details(show='name,data_fields')
        self.assertEquals(resp['model']['data_fields'], ['employer.country'])

    def test_download(self):
        def check(field, is_invalid=False):
            url = self._get_url(id=self.obj.id, action='download',
                                field=field)
            resp = self.client.get(url, headers=HTTP_HEADERS)
            if not is_invalid:
                self.assertEquals(resp.status_code, httplib.OK)
                self.assertEquals(resp.mimetype, 'text/plain')
                self.assertEquals(resp.headers['Content-Disposition'],
                                  'attachment; filename=%s-%s.json' %
                                  (self.obj.name, field))
            else:
                self.assertEquals(resp.status_code, 400)
        check('features')
        check('invalid', is_invalid=True)

    def test_post_without_name(self):
        self.check_edit({'importhandler': 'smth'}, error='name is required')
