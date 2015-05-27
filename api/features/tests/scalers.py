""" Unittests for scaler related classes. """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from utils import FeaturePredefinedItemsTestMixin, FeatureItemsTestMixin
from ..views import ScalerResource
from ..models import Feature, PredefinedScaler
from ..fixtures import PredefinedScalerData, FeatureData


class PredefinedScalersTests(FeaturePredefinedItemsTestMixin):
    """
    Tests of the Feature scalers API.
    """
    BASE_URL = '/cloudml/features/scalers/'
    RESOURCE = ScalerResource
    Model = PredefinedScaler
    datasets = (PredefinedScalerData, FeatureData)

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
    BASE_URL = '/cloudml/features/scalers/'
    datasets = (PredefinedScalerData, FeatureData)

    OBJECT_NAME = 'scaler'
    DATA = {'type': 'StandardScaler',
            'name': 'new scaler',
            'params': '{"copy": true}'}

    def setUp(self):
        super(FeatureScalersTests, self).setUp()
        self.feature = Feature.query.all()[0]

    def test_add(self):
        resp, obj = self._test_add(self.feature)
        self.assertEqual(obj, {'type': 'StandardScaler',
                               'params': {"copy": True}})

    def test_add_from_predefined(self):
        scaler = PredefinedScaler.query.all()[0]
        resp, obj = self._test_add_from_predefined(self.feature, scaler)
        self.assertEqual(obj['type'], scaler.type)

    def test_edit(self):
        feature = Feature.query.filter_by(
            name=FeatureData.complex_feature.name).one()
        self.assertTrue(feature.scaler, "Invalid fixtures")
        data = {'name': 'new scaler name',
                'type': 'MinMaxScaler',
                'params': '{"feature_range_max": 2}'}

        resp, obj = self._test_edit(feature, extra_data=data)
        self.assertEqual(obj, {'params': {'feature_range_max': 2},
                               'type': u'MinMaxScaler'})

    def test_edit_feature_scaler_from_predefined(self):
        scaler = PredefinedScaler.query.all()[0]
        resp, obj = self._test_edit_from_predefined(self.feature, scaler)
        self.assertEqual(obj['type'], scaler.type)
