import math

from unittest import TestCase
from api.ml_models.helpers.weights import calc_weights_css

__author__ = 'nader'


class HelpersTests(TestCase):

    def test_calc_weights_css_all_zeros(self):
        weights = [
            {'weight': 0.0, 'name': 'weight01', 'feature_weight': 0.0},
            {'weight': 0.0, 'name': 'weight02', 'feature_weight': 0.0}
        ]
        weights01 = calc_weights_css(weights, 'green')
        self.assertEqual(weights01, [
            {'transformed_weight': 0,
             'css_class': 'green darkest',
             'name': 'weight01', 'weight': 0.0,
             'feature_weight': 0.0},
            {'transformed_weight': 0,
             'css_class': 'green darkest',
             'name': 'weight02',
             'weight': 0.0,
             'feature_weight': 0.0}
        ])

    def test_calc_weights_css(self):
        weights = [
            {'weight': 0.0, 'name': 'weight01', 'feature_weight': 0.0},
            {'weight': 0.1, 'name': 'weight02', 'feature_weight': 0.0},
            {'weight': 0.01, 'name': 'weight03', 'feature_weight': 0.0},
            {'weight': 0.001, 'name': 'weight03', 'feature_weight': 0.0},
        ]
        weights01 = calc_weights_css(weights, 'green')
        self.assertEqual(weights01, [
            {'transformed_weight': math.log(0.1 / 0.001),
             'css_class': 'green darker', 'name': 'weight02',
             'weight': 0.1, 'feature_weight': 0.0},
            {'transformed_weight': math.log(0.01 / 0.001),
             'css_class': 'green light', 'name': 'weight03',
             'weight': 0.01, 'feature_weight': 0.0},
            {'transformed_weight': math.log(0.001 / 0.001),
             'css_class': 'green lightest', 'name': 'weight03',
             'weight': 0.001, 'feature_weight': 0.0},
            {'transformed_weight': 0, 'css_class': 'green lightest',
             'name': 'weight01', 'weight': 0.0, 'feature_weight': 0.0}
        ])
