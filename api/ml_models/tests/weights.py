import httplib
import math
import json
import random
import urllib
from moto import mock_s3

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..fixtures import WeightData, WeightsCategoryData
from ..models import Weight, WeightsCategory
from ..views import ModelResource
from api.ml_models.models import Model
from api.ml_models.fixtures import ModelData
from api.features.fixtures import FeatureSetData, FeatureData


class WeightResourceTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the WeightResource. """
    MODEL_NAME = 'weights_model'
    datasets = [FeatureData, FeatureSetData, ModelData,
                WeightsCategoryData, WeightData]

    def setUp(self):
        super(WeightResourceTests, self).setUp()
        self.model = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.BASE_URL = '/cloudml/weights/%s/' % self.model.id

    def test_list(self):
        data = self._check(per_page=2)
        self.assertTrue(data['has_next'])
        self.assertFalse(data['has_prev'])
        self.assertEquals(data['per_page'], 2)
        self.assertEquals(data['total'], 3)
        self.assertEquals(data['pages'], 2)
        self.assertTrue('weights' in data, data)
        self.assertEquals(data['total'],
                          Weight.query.filter_by(model=self.model).count())

    @mock_s3
    def test_search(self, *mocks):
        trained_model_name = 'Trained Model Full Text'

        with open('./conf/extract.json', 'r') as f:
            handler = f.read()
        with open('./api/ml_models/model.dat', 'r') as f:
            trainer = f.read()
        post_data = {'test_import_handler_file': handler,
                     'import_handler_file': handler,
                     'trainer': trainer,
                     'name': trained_model_name}
        resp = self.client.post('/cloudml/models/', data=post_data,
                                headers=HTTP_HEADERS)
        assert resp.status_code == httplib.CREATED
        self.model = Model.query.filter_by(name=trained_model_name).one()
        self.BASE_URL = '/cloudml/weights/%s/' % self.model.id

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'is_positive': -1,
            'order': 'asc',
            'page': 1,
            'show': 'name,value,css_class',
            'sort_by': 'name',
            'q': 'python'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertFalse(data['has_next'])
        self.assertFalse(data['has_prev'])
        self.assertEquals(data['per_page'], 20)
        self.assertTrue('weights' in data, data)
        self.assertFalse('tsexams->Ruby on Rails' in resp.data)
        self.assertTrue(
            'tsexams->Python 2.x Test' in data['weights'][0]['name'])

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'is_positive': 0,
            'order': 'asc',
            'page': 1,
            'show': 'name,value,css_class',
            'sort_by': 'name',
            'q': 'python'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue(
            'tsexams->Python 2.x Test' in data['weights'][0]['name'])

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'is_positive': 1,
            'order': 'asc',
            'page': 1,
            'show': 'name,value,css_class',
            'sort_by': 'name',
            'q': 'python'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue('tsexams->Python 2.x Test' in resp.data)
        self.assertFalse('tsexams->Ruby on Rails' in resp.data)

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'is_positive': 1,
            'order': 'asc',
            'page': 1,
            'show': 'name,value,css_class',
            'sort_by': 'name',
            'q': 'pythonic'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue('tsexams->Python 2.x Test' in resp.data)
        self.assertFalse('tsexams->Ruby on Rails' in resp.data)

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'is_positive': 1,
            'order': 'asc',
            'page': 1,
            'show': 'name,value,css_class',
            'sort_by': 'name',
            'q': 'pyth'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue('tsexams->Python 2.x Test' in resp.data)
        self.assertFalse('tsexams->Ruby on Rails' in resp.data)

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'is_positive': 1,
            'order': 'asc',
            'page': 1,
            'show': 'name,value,css_class',
            'sort_by': 'name',
            'q': '2.x'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue('tsexams->Python 2.x Test' in resp.data)
        self.assertFalse('tsexams->Ruby on Rails' in resp.data)

    def test_brief(self):
        data = self._check(action='brief')
        self.assertTrue('negative_weights' in data, data)
        self.assertTrue('positive_weights' in data, data)
        positive = data['positive_weights']
        negative = data['negative_weights']
        self.assertEquals(len(positive), 2)
        self.assertEquals(len(negative), 1)

    def test_invalid_methods(self):
        self._check_not_allowed_method('post')
        self._check_not_allowed_method('delete')
        self._check_not_allowed_method('put')


class WeightTreeResourceTests(BaseDbTestCase, TestChecksMixin):
    datasets = [FeatureData, FeatureSetData, ModelData, WeightData, WeightsCategoryData]

    def setUp(self):
        super(WeightTreeResourceTests, self).setUp()
        self.model = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.BASE_URL = '/cloudml/weights_tree/%s/' % self.model.id

    def test_tree(self):
        data = self._check()
        self.assertTrue('weights' in data, data)
        self.assertTrue('categories' in data, data)
        self.assertTrue('opening' in str(data), data)

        data = self._check(parent='contractor.dev_blurb')
        self.assertEquals(data['weights'][0]['name'], WeightData.weight_02.name)
        self.assertEquals(len(data['weights']), 1)

    def test_invalid_methods(self):
        self._check_not_allowed_method('post')
        self._check_not_allowed_method('delete')
        self._check_not_allowed_method('put')


class WeightTasksTests(BaseDbTestCase, TestChecksMixin):
    datasets = [FeatureData, FeatureSetData, ModelData]
    Model = Model
    RESOURCE = ModelResource
    BASE_URL = '/cloudml/models/'

    def setUp(self):
        super(WeightTasksTests, self).setUp()

    @mock_s3
    def test_fill_weights(self, *mocks):
        name = 'new2'
        handler = open('conf/extract.json', 'r').read()
        trainer = open('./api/ml_models/model.dat', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'import_handler_file': handler,
                     'trainer': trainer,
                     'name': name}
        resp, model = self.check_edit(post_data)
        self.assertEquals(model.name, name)
        self.assertEquals(model.status, model.STATUS_TRAINED)

        # Fill weights
        trainer = model.get_trainer()
        trainer_weights = trainer.get_weights()
        trainer_weight_list = trainer_weights['positive'] \
            + trainer_weights['negative']

        self.assertEquals(
            len(trainer_weight_list),
            Weight.query.filter_by(model=model).count())

        # Check categories in db
        cat = WeightsCategory.query.filter_by(
            model=model, name='contractor').one()
        self.assertEquals(cat.parent, '')
        self.assertEquals(cat.short_name, 'contractor')

        cat = WeightsCategory.query.filter_by(
            model=model, name='contractor.dev_profile_title').one()
        self.assertEquals(cat.parent, 'contractor')
        self.assertEquals(cat.short_name, 'dev_profile_title')

        # Check weights in db
        def check_random_weight():
            weight_dict = trainer_weight_list[
                random.choice(xrange(len(trainer_weight_list)))]
            weight = Weight.query.filter_by(
                model=model, name=weight_dict['name']).one()
            self.assertEquals(round(weight.value, 2),
                              round(weight_dict['weight'], 2))

        for i in xrange(5):
            check_random_weight()

        def check_weight(name, params):
            wgh = Weight.query.filter_by(
                model=model, name=name).one()
            self.assertTrue(wgh)
            for key, val in params.iteritems():
                self.assertEquals(getattr(wgh, key), val)

        check_weight('contractor->dev_blurb->best',
                     {'is_positive': False,
                      'short_name': 'best',
                      'css_class': 'red dark',
                      'parent': 'contractor.dev_blurb'})
