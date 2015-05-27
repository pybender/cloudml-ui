""" Unittests for utility methods and classes. """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import httplib
from copy import copy

from api.features.models import Feature
from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS


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
    def __run_check(self, feature, method, data):
        resp = self._check(data=data, method='post')
        feature = Feature.query.get(feature.id)
        inner_obj = getattr(feature, self.OBJECT_NAME)
        return resp, inner_obj

    def _test_add(self, feature, extra_data={}):
        data = copy(self.DATA)
        data.update({'feature_id': feature.id})
        data.update(extra_data)

        return self.__run_check(feature, 'post', data)

    def _test_add_from_predefined(self, feature, item):
        data = {self.OBJECT_NAME: item.name,
                'feature_id': feature.id,
                'predefined_selected': 'true'}

        return self.__run_check(feature, 'post', data)

    def _test_edit(self, feature, extra_data={}):
        data = copy(self.DATA)
        data.update({'feature_id': feature.id})
        data.update(extra_data)

        return self.__run_check(feature, 'put', data)

    def _test_edit_from_predefined(self, feature, predefined_item):
        data = {self.OBJECT_NAME: predefined_item.name,
                'feature_id': feature.id,
                'predefined_selected': 'true'}

        return self.__run_check(feature, 'post', data)

    def check_edit_error(self, post_data, errors, **data):
        from api.base.resources import ERR_INVALID_DATA
        url = self._get_url(**data)
        resp = self.client.post(url, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        resp_data = json.loads(resp.data)
        err_data = resp_data['response']['error']
        self.assertEquals(err_data['code'], ERR_INVALID_DATA)
        self._check_errors(err_data, errors)
