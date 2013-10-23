import json
import httplib
import logging
from bson import ObjectId

from utils import BaseTestCase, HTTP_HEADERS
from utils import MODEL_ID
from api import app
from api.views import FeatureResource


class TestFeatureResource(BaseTestCase):
    """
    Features API methods tests.
    """
    TRANSFORMER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('feature_sets.json', 'features.json',
                'models.json', 'transformers.json')
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

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            resp = self._check_post(data, error='err')
            self._check_errors(resp, errors)

        _check({}, errors={
            'name': 'name is required',
            'type': 'type is required',
            'features_set_id': 'features_set_id is required'})

        _check({"name": "contractor.dev_recent_hours"}, errors={
            'type': 'type is required',
            'features_set_id': 'features_set_id is required'})

        # Transformers data is invalid
        data = {
            "name": "contractor.dev_recent_hours",
            "type": "int",
            "features_set_id": self.model.features_set_id,
            'transformer-type': 'type',
            'transformer-params': 'aaa'
        }
        _check(data, errors={
            'transformer': "transformer-params: invalid json: aaa, \
transformer-type: should be one of Count, Tfidf, Dictionary"})

    def test_add_simple_feature(self):
        data = {
            "name": "contractor.dev_recent_hours",
            "type": "int",
            "features_set_id": self.model.features_set_id,
            "input_format": "choice",
            "default": "100",
            "required": True,
            "is_target_variable": True
        }
        resp, obj = self._check_post(data, load_model=True)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.features_set_id, data['features_set_id'])
        self.assertTrue(obj.required)
        self.assertTrue(obj.is_target_variable)
        self.assertEquals(obj.input_format, data['input_format'])
        self.assertEquals(obj.default, data['default'])

    def test_add_feature(self):
        """
        Adding feature with transformer and scaler
        """
        data = {
            "name": "title",
            "type": "text",
            "features_set_id": self.model.features_set_id,
            "transformer-type": "Count",
            "scaler-type": "MinMaxScaler"
        }
        resp, obj = self._check_post(data, load_model=True)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.features_set_id, data['features_set_id'])
        self.assertTrue(obj.transformer, "Transformer not created")
        self.assertEquals(obj.transformer['type'], data["transformer-type"])
        self.assertTrue(obj.scaler, "Scaler not created")
        self.assertEquals(obj.scaler['type'], data["scaler-type"])

        transformer = app.db.Transformer.find_one()
        data = {
            "name": "title",
            "type": "text",
            "features_set_id": self.model.features_set_id,
            "transformer-transformer": transformer.name,
            "transformer-predefined_selected": True
        }
        resp, obj = self._check_post(data, load_model=True)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.features_set_id, data['features_set_id'])
        from api.models import Transformer
        transformer = Transformer(obj.transformer)
        self.assertTrue(transformer, "Transformer not created")
        self.assertEquals(transformer.name, transformer.name)
        self.assertEquals(transformer.type, transformer.type)
        self.assertEquals(transformer.params, transformer.params)

    def test_inline_edit_feature(self):
        """
        Checking edditing of separate fields
        """
        data = {"name": "new name"}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.name, data['name'])

        data = {"type": "text"}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.type, data['type'])

        data = {"input_format": "dict"}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.input_format, data['input_format'])

        # TODO: default values could be int, dict, etc?
        data = {"default": "some text"}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.default, data['default'])

        data = {"required": True}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.required, data['required'])

    def test_edit_feature(self):
        """
        Tests edditing feature in separate page API call.
        """
        data = {"name": "some name",
                "type": "int",
                "transformer-type": "Dictionary",
                "scaler-type": "StandardScaler"}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertTrue(obj.transformer, "Transformer not filled")
        self.assertTrue(obj.transformer['type'], data['transformer-type'])
        self.assertTrue(obj.scaler, "scaler not filled")
        self.assertTrue(obj.scaler['type'], data['scaler-type'])

        data = {"name": "some name",
                "type": "int",
                "remove_transformer": True,
                "remove_scaler": True}
        resp, obj = self._check_put(data, load_model=True)
        self.assertFalse(obj.transformer, "Transformer should be removed")
        self.assertFalse(obj.scaler, "scaler should be removed")

    def test_make_target_variable(self):
        fset = self.model.features_set
        data = {'is_target_variable': 'true'}
        params = {'is_target_variable': False,
                  'features_set_id': str(fset._id)}
        feature = app.db.Feature.find_one(params)
        url = self._get_url(id=feature._id)
        resp = self.app.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)

        fset = app.db.FeatureSet.get_from_id(fset._id)
        self.assertEquals(feature.name, fset.target_variable)

        logging.debug('Target varialble is %s', feature.name)
        feature = app.db.Feature.get_from_id(feature._id)
        self.assertTrue(feature.is_target_variable)

        features = app.db.Feature.find(params)
        self.assertTrue(features.count())
        for f in features:
            self.assertFalse(f.is_target_variable)


class TestFeaturesDocs(BaseTestCase):
    """
    Tests for the FeatureSet and Feature models.
    """
    FIXTURES = ('complex_features.json', 'features.json', 'models.json', )

    def test_feature_to_dict(self):
        FeatureSet = app.db.FeatureSet
        Feature = app.db.Feature

        fset = FeatureSet()
        fset.schema_name = 'bestmatch'
        fset.save()

        feature = Feature()
        feature_data = {
            'features_set': fset,
            'features_set_id': str(fset._id),
            'name': 'name',
            'type': 'text',
            'required': False}
        fields_from_dict(feature, feature_data)
        feature.save()
        fdict = feature.to_dict()
        self.assertEquals(fdict, {'name': 'name',
                                  'type': 'text'})

        feature = app.db.Feature.find_one({'name': 'transformed feature'})
        fdict = feature.to_dict()
        self.maxDiff = None
        print fdict['scaler']
        self.assertEquals(fdict, {
            'scaler': {'copy': True,
                       'name': u'feature scaler #3',
                       'type': u'MinMaxScaler'},
            'transformer': {'charset': u'aaa1',
                            'name': u'Test count #2 not is_predefined',
                            'type': u'Count'},
            'name': u'transformed feature',
            'input-format': u'dict',
            'default': u'smth',
            'is-required': True,
            'params': {u'mappings': {u'class2': 0, u'class1': 1}},
            'type': u'map'})

    def test_manipulating_with_features(self):
        FeatureSet = app.db.FeatureSet
        Feature = app.db.Feature

        fset = FeatureSet()
        self.assertTrue(fset.features_dict)
        fset.schema_name = 'bestmatch'
        fset.save()
        self.assertEquals(fset.features_dict,
                          {'feature-types': [],
                           'features': [],
                           'schema-name': 'bestmatch'})
        feature1 = Feature()
        feature1_data = {
            'features_set': fset,
            'features_set_id': str(fset._id),
            'name': 'name',
            'type': 'text'}
        fields_from_dict(feature1, feature1_data)
        feature1.save()

        fset = FeatureSet.get_from_id(fset._id)
        self.assertFalse(fset.target_variable)
        self.assertEquals(fset.features_count, 1)
        self.assertEquals(len(fset.features_dict['features']), 1)
        feature2 = Feature()
        feature2_data = {
            'features_set': fset,
            'features_set_id': str(fset._id),
            'name': 'hire_outcome', 'type': 'int',
            'is_target_variable': True}
        fields_from_dict(feature2, feature2_data)
        fset = FeatureSet.get_from_id(fset._id)
        feature2.save()

        fset = FeatureSet.get_from_id(fset._id)
        self.assertEquals(fset.target_variable, 'hire_outcome')
        self.assertEquals(fset.features_count, 2)
        self.assertEquals(len(fset.features_dict['features']), 2)

        feature1 = Feature.get_from_id(feature1._id)
        feature1.name = 'feature_new_name'
        feature1.save()

        fset = FeatureSet.get_from_id(fset._id)
        self.assertEquals(fset.features_count, 2)
        self.assertEquals(len(fset.features_dict['features']), 2)
        self.assertTrue(
            'feature_new_name' in str(fset.features_dict['features']))

        feature1 = Feature.get_from_id(feature1._id)
        feature1.delete()
        fset = FeatureSet.get_from_id(fset._id)
        self.assertEquals(fset.features_count, 1)
        self.assertEquals(len(fset.features_dict['features']), 1)
        self.assertEquals(fset.features_dict['features'][0]['name'],
                          'hire_outcome')

    def test_load_from_features_dict(self):
        features_json = json.loads(open('./conf/features.json', 'r').read())

        from api.models import FeatureSet
        features_set = FeatureSet.\
            from_model_features_dict("Set", features_json)
        self.assertTrue(features_set)
        self.assertEquals(features_set.name, "Set")
        self.assertEquals(features_set.schema_name, 'bestmatch')
        self.assertEquals(features_set.features_count, 37)
        self.assertEquals(len(features_set.features_dict['features']), 37)
        self.assertEquals(features_set.target_variable, 'hire_outcome')

        # named features type "str_to_timezone" should be added
        ftype = app.db.NamedFeatureType.find_one({'name': 'str_to_timezone'})
        self.assertTrue(ftype, 'Named type not added')
        self.assertEquals(ftype.type, 'composite')
        self.assertEquals(ftype.params, {u'chain': [{
            u'params': {u'pattern': u'UTC([-\\+]+\\d\\d).*'},
            u'type': u'regex'},
            {u'type': u'int'}]})

        # Checking features
        params = {'features_set_id': str(features_set._id)}
        features = app.db.Feature.find(params)
        self.assertEquals(features.count(), 37)

        def _check_feature(name, fields):
            params = {'name': name,
                      'features_set_id': str(features_set._id)}
            params.update(params)
            feature = app.db.Feature.find_one(params)
            self.assertTrue(feature)
            for field, val in fields.iteritems():
                self.assertEquals(
                    feature[field], val,
                    'Field: %s: %s != %s' % (field, feature[field], val))
            return feature

        feature = _check_feature('hire_outcome', {
            'is_target_variable': True,
            'type': 'map',
            'params': {"mappings": {"class1": 1,
                                    "class2": 0}}}
        )

        feature = _check_feature('contractor.dev_blurb', {
            'is_target_variable': False,
            'type': 'text',
            'params': {},
            'required': True}
        )
        from api.models import Transformer
        transformer = Transformer(feature.transformer)

        self.assertTrue(transformer)
        self.assertEquals(transformer.type, 'Tfidf')
        self.assertEquals(transformer.params,
                          {u'ngram_range_max': 1,
                           u'ngram_range_min': 1,
                           u'min_df': 10})

        feature = _check_feature('tsexams', {
            'type': 'float',
            'params': {},
            'input_format': 'dict'}
        )

        feature = _check_feature('contractor.dev_last_worked',
                                 {'default': 946684800})
        feature = _check_feature('contractor.dev_year_exp',
                                 {'required': False})
        feature = _check_feature('employer.op_timezone',
                                 {'type': 'str_to_timezone'})


def fields_from_dict(obj, fields):
    for key, val in fields.iteritems():
        setattr(obj, key, val)
