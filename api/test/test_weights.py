import httplib
import math
import json
import random

from utils import BaseTestCase


class WeightsTests(BaseTestCase):
    """
    Tests of the Models Parameters Weights.
    """
    COUNT = 4556
    MODEL_NAME = 'weights_model'

    def setUp(self):
        super(WeightsTests, self).setUp()
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./model.dat', 'r')
        post_data = {'importhandler': handler,
                     'trainer': trainer}
        resp = self.app.post('/cloudml/model/%s' % self.MODEL_NAME,
                             data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.model = self.db.Model.find_one({'name': self.MODEL_NAME})
        trainer = self.model.get_trainer()
        weights = self.trainer_weights = trainer.get_weights()
        self.weight_list = weights['positive'] + weights['negative']
        self._LOADED_COLLECTIONS += ['WeightsCategory', 'Weight']

    def test_weights(self):
        self._check_weights_task()
        self._check_categories_in_db()
        self._check_weights_in_db()

        # Checking API responses
        self._check_list()
        self._check_tree()

    def _check_weights_task(self):
        from api.tasks import fill_model_parameter_weights
        res = fill_model_parameter_weights.run(self.model.name,
                                               **self.trainer_weights)
        self.assertEquals(res, 'Model weights_model parameters weights \
was added to db: %s' % self.COUNT)
        count = self.db.Weight.find({'model_name': self.model.name}).count()
        self.assertEquals(count, self.COUNT)

    def _check_categories_in_db(self):
        cat = self.db.WeightsCategory.find_one({'model_name': self.MODEL_NAME,
                                                'name': 'opening'})
        self.assertEquals(cat['parent'], '')
        self.assertEquals(cat['short_name'], 'opening')

        cat = self.db.WeightsCategory.find_one({'model_name': self.MODEL_NAME,
                                                'name': 'opening.type'})
        self.assertEquals(cat['parent'], 'opening')
        self.assertEquals(cat['short_name'], 'type')

    def _check_weights_in_db(self):
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

        check_weight('opening->skills->authorize.net',
                     {'is_positive': False,
                      'short_name': 'authorize.net',
                      'css_class': 'red lightest',
                      'parent': 'opening.skills',
                      'value': 0})

    def _check_list(self):
        resp = self.app.get('/cloudml/weights/%s' % self.MODEL_NAME)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue(data['has_next'])
        self.assertFalse(data['has_prev'])
        self.assertEquals(data['per_page'], 20)
        self.assertEquals(data['total'], self.COUNT)
        self.assertEquals(data['pages'], math.ceil(1.0 * self.COUNT / 20))
        self.assertTrue('weights' in data, data)
        self.assertTrue('employer->country->singapore' in resp.data)

    def _check_tree(self):
        resp = self.app.get('/cloudml/weights_tree/%s' % self.MODEL_NAME)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('weights' in data, data)
        self.assertTrue('categories' in data, data)
        self.assertTrue('matches_pref_test' in resp.data, resp.data)
        self.assertTrue('opening' in resp.data, resp.data)
