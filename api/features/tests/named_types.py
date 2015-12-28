""" Unittests for named feature types related classes and functions. """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json

from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from ..views import NamedTypeResource
from ..models import NamedFeatureType
from ..fixtures import NamedFeatureTypeData


class NamedFeatureTypeTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Feature types API.
    """
    BASE_URL = '/cloudml/features/named_types/'
    RESOURCE = NamedTypeResource
    Model = NamedFeatureType
    datasets = (NamedFeatureTypeData, )

    def setUp(self):
        super(NamedFeatureTypeTests, self).setUp()
        self.obj = self.Model.query.all()[0]

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        self.check_details()

    def test_post(self):
        post_data = {'type': 'int',
                     'name': 'new'}
        resp, obj = self.check_edit(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.type, post_data['type'])

    def test_post_composite(self):
        data = {'type': 'composite',
                'name': 'new-composite'}
        self.check_edit_error(data, errors={
            'params': 'Parameters are required for type composite, '
                      'but were not specified'}
        )

        data = {'type': 'composite',
                'name': 'new-composite',
                'params': 'invalid'}
        self.check_edit_error(data, errors={
            'params': "JSON file is corrupted. Can not load it: invalid"}
        )

        data = {'type': 'composite',
                'name': 'new-composite',
                'params': '{}'}
        self.check_edit_error(data, errors={
            'params': "Parameter chain is required"}
        )

        data = {'type': 'composite',
                'name': 'new-composite',
                'params': '{"chain": {}}'}
        self.check_edit_error(data, errors={
            'type': "Cannot create instance of feature type: "
                    "Composite feature types should define a "
                    "list of individual feature types"}
        )

        data = {'type': 'composite',
                'name': 'new-composite',
                'params': '{"chain": [{"type": "int"}, {"type": "float"}]}'}
        resp, obj = self.check_edit(data, load_model=True)
        self.assertEqual(obj.name, data['name'])
        self.assertEqual(obj.type, data['type'])
        self.assertEqual(obj.params, json.loads(data['params']))
