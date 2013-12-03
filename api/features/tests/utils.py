import json
from copy import copy

from api.features.models import Feature
from api.base.test_utils import BaseDbTestCase, TestChecksMixin


class FeaturePredefinedItemsTestMixin(BaseDbTestCase, TestChecksMixin):
    OBJECT_NAME = None
    DATA = {}

    def _test_add(self, extra_data={}):
        data = copy(self.DATA)
        data.update(extra_data)

        resp, obj = self.check_edit(data)
        self.assertEqual(obj.name, data['name'])
        self.assertEqual(obj.type, data['type'])
        self.assertEqual(obj.params, json.loads(data['params']))
        return resp, obj

    def _test_edit(self, obj=None):
        if obj is None:
            obj = self.obj

        data = copy(self.DATA)
        data['name'] = 'new'
        resp, obj = self.check_edit(data, id=obj.id)
        self.assertEquals(obj.name, 'new')
        self.assertEquals(obj.type, data['type'])
        return resp, obj


class FeatureItemsTestMixin(BaseDbTestCase, TestChecksMixin):
    def _test_add_feature_item(self, feature, extra_data={}):
        data = copy(self.DATA)
        data.update({'feature_id': str(feature._id)})
        data.update(extra_data)

        self._check_post(data, load_model=False, inner_obj=True)
        feature = Feature.get_from_id(feature._id)
        obj = getattr(feature, self.OBJECT_NAME)
        self.assertEqual(obj['type'], data['type'])
        self.assertEqual(obj['params'], json.loads(data['params']))

    def _add_feature_item_from_predefined(self, feature, item):
        data = {self.OBJECT_NAME: item.name,
                'feature_id': str(feature._id),
                'predefined_selected': 'true'}
        self._check_post(data, load_model=False, inner_obj=True)
        feature = Feature.get_from_id(feature._id)
        obj = getattr(feature, self.OBJECT_NAME)
        self.assertEqual(obj['type'], item.type)
        self.assertEqual(obj['params'], item.params)

    def _test_edit_feature_item(self, feature, extra_data={}):
        data = copy(self.DATA)
        data.update({'feature_id': str(feature._id)})
        data.update(extra_data)

        resp = self._check_put(data)
        feature = Feature.get_from_id(feature._id)
        obj = getattr(feature, self.OBJECT_NAME)
        self.assertEqual(obj['name'], data['name'])
        self.assertEqual(obj['type'], data['type'])
        self.assertEqual(obj['params'], json.loads(data['params']))

        return resp, obj

    def _edit_feature_item_from_predefined(self, feature, predefined_item):
        data = {self.OBJECT_NAME: predefined_item.name,
                'feature_id': str(feature._id),
                'predefined_selected': 'true'}
        resp = self._check_put(data, load_model=False)
        feature = self.db.Feature.find_one({'_id': feature._id})
        self.assertTrue(getattr(feature, self.OBJECT_NAME),
                        "%s should be filled" % self.OBJECT_NAME)

        obj = getattr(feature, self.OBJECT_NAME)
        self.assertEqual(obj['name'], predefined_item.name)
        self.assertEqual(obj['type'], predefined_item.type)
        self.assertEqual(obj['params'], predefined_item.params)
        return resp, obj
