import logging
from bson import ObjectId

from utils import FeaturePredefinedItems, HTTP_HEADERS
from api.views import ScalersResource


class ScalersTests(FeaturePredefinedItems):
    """
    Tests of the Feature scalers API.
    """
    ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('features.json', 'scalers.json', 'complex_features.json')
    BASE_URL = '/cloudml/features/scalers/'
    RESOURCE = ScalersResource

    OBJECT_NAME = 'scaler'
    DATA = {'type': 'StandardScaler',
            'name': 'new scaler',
            'params': '{"copy": true}'}

    def setUp(self):
        super(ScalersTests, self).setUp()
        self.Model = self.db.Scaler
        self.obj = self.Model.get_from_id(ObjectId(self.ID))
        self.assertTrue(self.obj)

    def test_list(self):
        self._check_list(show='name')

    def test_details(self):
        self._check_details()

    def test_add_predefined_scaler(self):
        self._test_add_predefined()

    def test_add_feature_scaler(self):
        feature = self.db.Feature.find_one()
        self._test_add_feature_item(feature)

    def test_add_feature_scaler_from_predefined(self):
        feature = self.db.Feature.find_one()
        scaler = self.db.Scaler.find_one({'is_predefined': True})
        self._add_feature_item_from_predefined(feature, scaler)

    def test_edit_predefined_scaler(self):
        self._test_edit_predefined_item()

    def test_edit_feature_scaler(self):
        feature = self.db.Feature.get_from_id(
            ObjectId('525123b1206a6c5bcbc12efb'))
        self.assertTrue(feature.scaler, "Invalid fixtures")
        data = {'name': 'new scaler name',
                'type': 'MinMaxScaler',
                'params': '{"feature_range_max": 2}'}

        resp, obj = self._test_edit_feature_item(feature, extra_data=data)
        self.assertTrue(obj.params, {"feature_range_max": 2})

    def test_edit_feature_scaler_from_predefined(self):
        feature = self.db.Feature.get_from_id(
            ObjectId('525123b1206a6c5bcbc12efb'))
        self.assertTrue(feature.scaler, "Invalid fixtures")

        scaler = self.db.Scaler.find_one({'is_predefined': True})
        self._edit_feature_item_from_predefined(feature, scaler)

    def test_delete_predefined_scaler(self):
        self._check_delete()

    def test_delete_feature_scaler(self):
        """
        Check that we can't delete feature scaler
        """
        feature = self.db.Feature.get_from_id(
            ObjectId('525123b1206a6c5bcbc12efb'))
        self.assertTrue(feature.scaler, "Invalid fixtures")
        self.assertFalse(feature.scaler.is_predefined)

        url = self._get_url(id=feature.scaler._id)
        resp = self.app.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 400)
