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
    FIXTURES = ['features.json', 'models.json', 'transformers.json']
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
        self.assertTrue(obj.features_set, "Feature set not filled")
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
        self.assertTrue(obj.features_set, "Feature set not filled")
        self.assertTrue(obj.transformer, "Transformer not created")
        self.assertEquals(obj.transformer.type, data["transformer-type"])
        self.assertFalse(obj.transformer.is_predefined)
        self.assertTrue(obj.scaler, "Scaler not created")
        self.assertEquals(obj.scaler.type, data["scaler-type"])
        self.assertFalse(obj.scaler.is_predefined)

        transformer = app.db.Transformer.find_one({'is_predefined': True})
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
        self.assertTrue(obj.features_set, "Feature set not filled")
        self.assertTrue(obj.transformer, "Transformer not created")
        self.assertEquals(obj.transformer.name, transformer.name)
        self.assertEquals(obj.transformer.type, transformer.type)
        self.assertEquals(obj.transformer.params, transformer.params)
        self.assertFalse(obj.transformer.is_predefined)

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
        self.assertTrue(obj.transformer.type, data['transformer-type'])
        self.assertTrue(obj.scaler, "scaler not filled")
        self.assertTrue(obj.scaler.type, data['scaler-type'])

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


class TestFeatureSetDoc(BaseTestCase):
    """
    Tests for the FeatureSet methods.
    """
    FIXTURES = ('models.json', )

    def test_from_model_features_dict(self):
        model = app.db.Model.get_from_id(ObjectId(MODEL_ID))

        from api.models import FeatureSet
        features_set = FeatureSet.\
            from_model_features_dict("Set", model.features)
        self.assertTrue(features_set)
        self.assertEquals(features_set.name, "Set")
        self.assertEquals(features_set.schema_name, 'bestmatch')
        self.assertEquals(features_set.features_count, 37)
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
            params = {'name': name}
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
        self.assertEquals(str(feature.features_set._id),
                          str(features_set._id))

        feature = _check_feature('contractor.dev_blurb', {
            'is_target_variable': False,
            'type': 'text',
            'params': {},
            'required': True}
        )
        transformer = feature.transformer
        self.assertTrue(transformer)
        self.assertEquals(transformer.name, 'contractor.dev_blurb-transformer')
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
