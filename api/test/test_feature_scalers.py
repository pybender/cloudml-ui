from utils import FeaturePredefinedItems
from api.views import ScalersResource


class ScalersTests(FeaturePredefinedItems):
    """
    Tests of the Feature scalers API.
    """
    ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('features.json', 'scalers.json', )
    BASE_URL = '/cloudml/features/scalers/'
    RESOURCE = ScalersResource

    OBJECT_NAME = 'scaler'
    DATA = {'type': 'StandardScaler',
            'name': 'new scaler',
            'params': '{"copy": true}'}

    def setUp(self):
        super(ScalersTests, self).setUp()
        self.Model = self.db.Scaler
        from bson import ObjectId
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

    def add_feature_scaler_from_predefined(self):
        feature = self.db.Feature.find_one()
        scaler = self.db.Scaler.find_one({'is_predefined': True})
        self._add_feature_item_from_predefined(feature, scaler)
