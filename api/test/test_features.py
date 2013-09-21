import httplib
import json
from bson import ObjectId

from utils import BaseTestCase, HTTP_HEADERS
from utils import MODEL_ID
from api.views import NamedFeatureTypeResource
from api import app


class NamedFeatureTypeTests(BaseTestCase):
    """
    Tests of the Instances API.
    """
    NAMED_TYPE_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('named_feature_types.json', )
    BASE_URL = '/cloudml/features/named_types/'
    RESOURCE = NamedFeatureTypeResource

    def setUp(self):
        super(NamedFeatureTypeTests, self).setUp()
        self.Model = self.db.NamedFeatureType
        self.obj = self.Model.get_from_id(ObjectId(self.NAMED_TYPE_ID))
        self.assertTrue(self.obj)

    def test_list(self):
        self._check_list(show='name')

    def test_details(self):
        self._check_details()

    def test_post(self):
        post_data = {'type': 'int',
                     'name': 'new'}
        resp, obj = self._check_post(post_data, load_model=True)
        self.assertEqual(obj.name, post_data['name'])
        self.assertEqual(obj.type, post_data['type'])


class TestFeaturesDoc(BaseTestCase):
    """
    Tests for the Model methods.
    """
    MODEL_NAME = 'TrainedModel'
    FIXTURES = ('models.json', )

    def test_from_model_features_dict(self):
        model = app.db.Model.get_from_id(ObjectId(MODEL_ID))

        features_set = app.db.FeatureSet.from_model_features_dict(model)
        self.assertTrue(features_set)
        self.assertEquals(features_set.name, '%s features' % model.name)
        self.assertEquals(features_set.schema_name, 'bestmatch')
        self.assertEquals(features_set.features_count, 37)
        self.assertEquals(features_set.target_variable, 'hire_outcome')

        self.assertTrue(features_set.classifier, 'Classifier not set')
        classifier = features_set.classifier
        self.assertEquals(classifier.name, '%s classifier' % model.name)
        self.assertEquals(classifier.type, 'logistic regression')
        self.assertEquals(classifier.params, {"penalty": "l2"})

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
