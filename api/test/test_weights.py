import httplib
import math
import json
import random

from utils import BaseTestCase, HTTP_HEADERS
from api import app


class WeightsTests(BaseTestCase):
    """
    Tests of the Models Parameters Weights.
    """
    MODEL_NAME = 'weights_model'

    @classmethod
    def setUpClass(cls):
        super(WeightsTests, cls).setUpClass()
        cls.fixtures_load()

        # POST Trained Model
        cls.post_trained_model(cls.MODEL_NAME)
        cls.model = app.db.Model.find_one({'name': cls.MODEL_NAME})
        cls.BASE_URL = '/cloudml/weights/%s/' % cls.model._id

        # Fill weights
        trainer = cls.model.get_trainer()
        weights = cls.trainer_weights = trainer.get_weights()
        cls.weight_list = weights['positive'] + weights['negative']
        cls.COUNT = len(cls.weight_list)
        cls._LOADED_COLLECTIONS += ['WeightsCategory', 'Weight']

    @classmethod
    def tearDownClass(cls):
        cls.fixtures_cleanup()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def _run_fill_model_weights_task(cls):
        from api.tasks import fill_model_parameter_weights
        fill_model_parameter_weights.run(str(cls.model._id),
                                         **cls.trainer_weights)
        count = app.db.Weight.find({'model_name': cls.model.name}).count()
        print count
        assert count == cls.COUNT

    def test_categories_in_db(self):
        cat = self.db.WeightsCategory.find_one({'model_name': self.MODEL_NAME,
                                                'model_id': str(self.model._id),
                                                'name': 'contractor'})
        self.assertEquals(cat['parent'], '')
        self.assertEquals(cat['short_name'], 'contractor')

        cat = self.db.WeightsCategory.find_one({'model_name': self.MODEL_NAME,
                                                'name': 'contractor.dev_profile_title'})
        self.assertEquals(cat['parent'], 'contractor')
        self.assertEquals(cat['short_name'], 'dev_profile_title')

    def test_weights_in_db(self):
        def check_random_weight():
            weight_dict = self.weight_list[random.choice(xrange(self.COUNT))]
            weight = self.db.Weight.find_one({'model_name': self.MODEL_NAME,
                                              'name': weight_dict['name']})
            self.assertEquals(weight['value'], weight_dict['weight'])

        check_random_weight()

        def check_weight(name, params):
            wgh = self.db.Weight.find_one({'model_name': self.MODEL_NAME,
                                           'name': name})
            self.assertTrue(wgh)
            for key, val in params.iteritems():
                self.assertEquals(wgh[key], val)

        check_weight('contractor->dev_blurb->best',
                     {'is_positive': False,
                      'short_name': 'best',
                      'css_class': 'red dark',
                      'parent': 'contractor.dev_blurb',
                      'value': -0.07864226503356551})

    def test_list(self):
        resp = self.app.get(self.BASE_URL, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue(data['has_next'])
        self.assertFalse(data['has_prev'])
        self.assertEquals(data['per_page'], 20)
        self.assertEquals(data['total'], self.COUNT)
        self.assertEquals(data['pages'], math.ceil(1.0 * self.COUNT / 20))
        self.assertTrue('weights' in data, data)
        self.assertTrue('tsexams->Ruby on Rails' in resp.data)

    def test_tree(self):
        resp = self.app.get('/cloudml/weights_tree/%s' % self.model._id,
                            headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('weights' in data, data)
        self.assertTrue('categories' in data, data)
        self.assertTrue('country_pair' in resp.data, resp.data)
        self.assertTrue('opening' in resp.data, resp.data)
