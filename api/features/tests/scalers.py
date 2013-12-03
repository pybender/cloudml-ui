from utils import FeaturePredefinedItemsTestMixin, FeatureItemsTestMixin
from ..views import ScalersResource
from ..models import Feature, PredefinedScaler
from ..fixtures import PredefinedScalerData


class PredefinedScalersTests(FeaturePredefinedItemsTestMixin):
    """
    Tests of the Feature scalers API.
    """
    ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('feature_sets.json', 'features.json',
                'scalers.json', 'complex_features.json')
    BASE_URL = '/cloudml/features/scalers/'
    RESOURCE = ScalersResource
    Model = PredefinedScaler
    datasets = (PredefinedScalerData, )

    OBJECT_NAME = 'scaler'
    DATA = {'type': 'StandardScaler',
            'name': 'new scaler',
            'params': '{"copy": true}'}

    def setUp(self):
        super(PredefinedScalersTests, self).setUp()
        self.obj = self.Model.query.all()[0]
        self.assertTrue(self.obj)

    def test_list(self):
        self.check_list(show='name')

    def test_details(self):
        resp = self.check_details(
            show='name,ip,is_default,type', obj=self.obj)
        scaler_resp = resp['scaler']
        self.assertEqual(scaler_resp['name'], self.obj.name)
        self.assertEqual(scaler_resp['type'], self.obj.type)

    def test_add(self):
        self._test_add()

    def test_edit(self):
        self._test_edit()

    def test_delete_predefined_scaler(self):
        self.check_delete()


class FeatureScalersTests(FeatureItemsTestMixin):
    def test_add_feature_scaler(self):
        feature = self.db.Feature.find_one()
        self._test_add_feature_item(feature)

    def test_add_feature_scaler_from_predefined(self):
        feature = self.db.Feature.find_one()
        scaler = self.db.Scaler.find_one()
        self._add_feature_item_from_predefined(feature, scaler)

    def test_edit_feature_scaler(self):
        feature = Feature.get_from_id(
            ObjectId('525123b1206a6c5bcbc12efb'))
        self.assertTrue(feature.scaler, "Invalid fixtures")
        data = {'name': 'new scaler name',
                'type': 'MinMaxScaler',
                'params': '{"feature_range_max": 2}'}

        resp, obj = self._test_edit_feature_item(feature, extra_data=data)

    def test_edit_feature_scaler_from_predefined(self):
        feature = self.db.Feature.get_from_id(
            ObjectId('525123b1206a6c5bcbc12efb'))
        self.assertTrue(feature.scaler, "Invalid fixtures")

        scaler = self.db.Scaler.find_one()
        self._edit_feature_item_from_predefined(feature, scaler)
