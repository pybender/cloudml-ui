from bson import ObjectId

from utils import BaseTestCase
from utils import MODEL_ID
from api import app
from api.views import FeatureResource


class TestFeatureResource(BaseTestCase):
    """
    Features API methods tests.
    """
    TRANSFORMER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ['features.json', 'models.json']
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = FeatureResource

    def setUp(self):
        super(TestFeatureResource, self).setUp()
        self.Model = self.db.Feature
        self.model = self.db.Model.find_one({'_id': ObjectId(MODEL_ID)})
        self.assertTrue(self.model)
        self.assertTrue(self.model.features_set)

        self.BASE_URL = '/cloudml/features/%s/items/' % \
            self.model.features_set._id

        self.obj = self.db.Feature.find_one()
        self.assertTrue(self.obj)

    def test_post(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            resp = self._check_post(data, error='required')
            self._check_errors(resp, errors)

        _check({}, errors={
            'name': 'name is required',
            'type': 'type is required',
            'features_set_id': 'features_set_id is required'})

        _check({"name":"contractor.dev_recent_hours"}, errors={
            'type': 'type is required',
            'features_set_id': 'features_set_id is required'})
        # data = {
        #     "name":"contractor.dev_recent_hours",
        #     "type":"int",
        #     "features_set_id": self.model.features_set_id
        # }
        # resp, feature = self._check_post(data, load_model=True)
        # self.assertEquals(feature.name, data['name'])
        # self.assertEquals(feature.type, data['type'])
        # self.assertEquals(feature.features_set_id, data['features_set_id'])


class TestFeatureSetDoc(BaseTestCase):
    """
    Tests for the FeatureSet methods.
    """
    FIXTURES = ('models.json', )

    def test_from_model_features_dict(self):
        model = app.db.Model.get_from_id(ObjectId(MODEL_ID))

        from api.models import FeatureSet
        features_set = FeatureSet.from_model_features_dict("Set", model.features)
        self.assertTrue(features_set)
        self.assertEquals(features_set.name, "Set")
        self.assertEquals(features_set.schema_name, 'bestmatch')
        self.assertEquals(features_set.features_count, 37)
        self.assertEquals(features_set.target_variable, 'hire_outcome')

        # named features type "str_to_timezone" should be added
        ftype = app.db.NamedFeatureType.find_one({'name': 'str_to_timezone'})
        self.assertTrue(ftype, 'Named type not added')
        self.assertEquals(ftype.type, 'composite')
        self.assertEquals(ftype.params,
                          {u'chain': [{u'params': \
{u'pattern': u'UTC([-\\+]+\\d\\d).*'}, u'type': u'regex'},
{u'type': u'int'}]})

        # Checking features
        params = {'features_set_id': str(features_set._id)}
        features = app.db.Feature.find(params)
        self.assertEquals(features.count(), 37)

        def _check_feature(name, fields):
            params = {'name': name}
            params.update(params)
            feature = app.db.Feature.find_one(params)
            self.assertTrue(feature)
            for field, val in fields.iteritems():
                self.assertEquals(feature[field], val,
                    'Field: %s: %s != %s' % (field, feature[field], val))
            return feature

        feature = _check_feature('hire_outcome',
            {
            'is_target_variable': True,
            'type': 'map',
            'params': {"mappings": {"class1": 1,
                                    "class2": 0 }
                      }
            }
        )
        self.assertEquals(str(feature.features_set._id), 
                          str(features_set._id))

        feature = _check_feature('contractor.dev_blurb',
            {
            'is_target_variable': False,
            'type': 'text',
            'params': {},
            'required': True
            }
        )
        transformer = feature.transformer
        self.assertTrue(transformer)
        self.assertEquals(transformer.name, 'contractor.dev_blurb-transformer')
        self.assertEquals(transformer.type, 'Tfidf')
        self.assertEquals(transformer.params,
                          {u'ngram_range_max': 1,
                           u'ngram_range_min': 1,
                           u'min_df': 10})

        feature = _check_feature('tsexams',
            {
            'type': 'float',
            'params': {},
            'input_format': 'dict' 
            }
        )

        feature = _check_feature('contractor.dev_last_worked',
                                 {'default': 946684800})
        feature = _check_feature('contractor.dev_year_exp',
                                 {'required': False})
        feature = _check_feature('employer.op_timezone',
                                 {'type': 'str_to_timezone'})
