""" Unittests for named feature types related classes and functions. """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

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
