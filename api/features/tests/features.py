import json
import httplib
import logging

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from ..views import FeatureResource
from ..models import Feature, FeatureSet, PredefinedTransformer, NamedFeatureType
from ..fixtures import FeatureSetData, FeatureData, PredefinedTransformerData
from api.ml_models.models import Model
from api.ml_models.fixtures import ModelData
from api.base.models import db


class TestFeatureResource(BaseDbTestCase, TestChecksMixin):
    """
    Features API methods tests.
    """
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = FeatureResource
    Model = Feature
    datasets = (FeatureSetData, FeatureData, ModelData,
                PredefinedTransformerData)

    def setUp(self):
        BaseDbTestCase.setUp(self)
        self.model = Model.query.filter_by(name=ModelData.model_01.name)[0]
        # TODO: Fix this
        fset = FeatureSet.query.filter_by(
            schema_name=FeatureSetData.bestmatch.schema_name)[0]
        self.model.features_set = fset
        self.model.save()

        self.BASE_URL = '/cloudml/features/%s/items/' % \
            self.model.features_set.id

        self.obj = Feature.query.filter_by(name=FeatureData.smth.name)[0]
        self.obj.feature_set = fset
        self.obj.save()

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.debug("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

        _check({}, errors={
            'name': 'name is required',
            'type': 'type is required',
            'feature_set_id': 'feature_set_id is required'})

        _check({"name": "contractor.dev_recent_hours"}, errors={
            'type': 'type is required',
            'feature_set_id': 'feature_set_id is required'})

        # Transformers data is invalid
        data = {
            "name": "contractor.dev_recent_hours",
            "type": "int",
            "feature_set_id": self.model.features_set_id,
            'transformer-type': 'type',
            'transformer-params': 'aaa'
        }
        _check(data, errors={
            'transformer': "transformer-params: invalid json: aaa, \
transformer-type: should be one of Count, Tfidf, Lda, Dictionary, Lsi"})

    def test_add_simple_feature(self):
        data = {
            "name": "contractor.dev_recent_hours",
            "type": "int",
            "feature_set_id": self.model.features_set_id,
            "input_format": "choice",
            "default": "100",
            "required": True,
            "is_target_variable": True
        }
        resp, obj = self.check_edit(data)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.feature_set_id, data['feature_set_id'])
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
            "feature_set_id": self.model.features_set_id,
            "transformer-type": "Count",
            "scaler-type": "MinMaxScaler"
        }
        resp, obj = self.check_edit(data)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.feature_set_id, data['feature_set_id'])
        self.assertTrue(obj.transformer, "Transformer not created")
        self.assertEquals(obj.transformer['type'], data["transformer-type"])
        self.assertTrue(obj.scaler, "Scaler not created")
        self.assertEquals(obj.scaler['type'], data["scaler-type"])

        transformer = PredefinedTransformer.query.all()[0]
        data = {
            "name": "title",
            "type": "text",
            "feature_set_id": self.model.features_set_id,
            "transformer-transformer": transformer.name,
            "transformer-predefined_selected": True
        }
        resp, obj = self.check_edit(data)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.feature_set_id, data['feature_set_id'])

        self.assertTrue(obj.transformer, "Transformer not added to feature")
        self.assertEquals(obj.transformer['type'], transformer.type)
        self.assertEquals(obj.transformer['params'], transformer.params)

    def test_inline_edit_feature(self):
        """
        Checking edditing of separate fields
        """
        data = {"name": "new name"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.name, data['name'])

        data = {"type": "text"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.type, data['type'])

        data = {"input_format": "dict"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.input_format, data['input_format'])

        # TODO: default values could be int, dict, etc?
        data = {"default": "some text"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.default, data['default'])

        data = {"required": True}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.required, data['required'])

    def test_edit_feature(self):
        """
        Tests edditing feature in separate page API call.
        """
        data = {"name": "some name",
                "type": "int",
                "transformer-type": "Dictionary",
                "scaler-type": "StandardScaler"}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])

        self.assertTrue(obj.transformer, "Transformer not filled")
        self.assertTrue(obj.transformer['type'], data['transformer-type'])
        self.assertTrue(obj.scaler, "Scaler not filled")
        self.assertTrue(obj.scaler['type'], data['scaler-type'])

        data = {"name": "some name",
                "type": "int",
                "remove_transformer": True,
                "remove_scaler": True}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertFalse(obj.transformer,
                         "Transformer should be removed (%s)" % obj.transformer)
        self.assertFalse(obj.scaler, "scaler should be removed")

    def test_make_target_variable(self):
        fset = self.model.features_set

        # TODO: Fix this hack. use refs in fixtures
        Feature.query.update(dict(feature_set_id=fset.id))

        data = {'is_target_variable': 'true'}
        params = {'is_target_variable': False,
                  'feature_set_id': str(fset.id)}
        feature = Feature.query.filter_by(**params)[0]
        resp, feature = self.check_edit(data, id=feature.id)

        fset = FeatureSet.query.get(fset.id)
        self.assertEquals(feature.name, fset.target_variable)

        logging.debug('Target varialble is %s', feature.name)
        feature = Feature.query.get(feature.id)
        self.assertTrue(feature.is_target_variable)

        features = Feature.query.filter_by(**params)
        self.assertTrue(features.count())
        for f in features:
            self.assertFalse(f.is_target_variable)


class TestFeaturesDocs(BaseDbTestCase):
    """
    Tests for the FeatureSet and Feature models.
    """
    datasets = (FeatureData, )

    def test_feature_to_dict(self):
        fset = FeatureSet()
        fset.schema_name = 'bestmatch'
        fset.save()

        feature = Feature()
        feature_data = {
            'feature_set': fset,
            'feature_set_id': fset.id,
            'name': 'name',
            'type': 'text',
            'required': False}
        fields_from_dict(feature, feature_data)
        feature.save()
        fdict = feature.to_dict()
        self.assertEquals(fdict, {'name': 'name',
                                  'type': 'text'})

        feature = Feature.query.filter_by(
            name='transformed feature')[0]
        fdict = feature.to_dict()
        self.maxDiff = None
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
        fset = FeatureSet()

        def expire_fset():
            db.session.expire(
                fset, ['target_variable','features_count', 'features_dict'])

        fset.schema_name = 'bestmatch'
        fset.save()
        self.assertTrue(fset.features_dict)
        self.assertEquals(fset.features_count, 0)

        self.assertEquals(fset.features_dict,
                          {'feature-types': [],
                           'features': [],
                           'schema-name': 'bestmatch'})
        feature1 = Feature()
        feature1_data = {
            'feature_set': fset,
            'name': 'name',
            'type': 'text'}
        fields_from_dict(feature1, feature1_data)
        feature1.save()

        expire_fset()
        self.assertFalse(fset.target_variable)
        self.assertEquals(fset.features_count, 1)
        self.assertEquals(len(fset.features_dict['features']), 1)

        feature2 = Feature()
        feature2_data = {
            'feature_set': fset,
            'name': 'hire_outcome', 'type': 'int',
            'is_target_variable': True}
        fields_from_dict(feature2, feature2_data)
        feature2.save()

        expire_fset()
        self.assertEquals(fset.features_count, 2)
        self.assertEquals(fset.target_variable, 'hire_outcome')
        self.assertEquals(len(fset.features_dict['features']), 2)

        feature1 = Feature.query.get(feature1.id)
        feature1.name = 'feature_new_name'
        feature1.save()

        expire_fset()
        self.assertEquals(fset.features_count, 2)
        self.assertEquals(len(fset.features_dict['features']), 2)
        self.assertTrue(
            'feature_new_name' in str(fset.features_dict['features']))

        feature1 = Feature.query.get(feature1.id)
        feature1.delete()
        fset = FeatureSet.query.get(fset.id)
        self.assertEquals(fset.features_count, 1)
        self.assertEquals(len(fset.features_dict['features']), 1)
        self.assertEquals(fset.features_dict['features'][0]['name'],
                          'hire_outcome')

    def test_load_from_features_dict(self):
        features_json = json.loads(open('./conf/features.json', 'r').read())
        feature_set = FeatureSet.\
            from_model_features_dict("Set", features_json)
        self.assertTrue(feature_set)
        self.assertEquals(feature_set.schema_name, 'bestmatch')
        self.assertEquals(len(feature_set.features_dict['features']), 37)
        self.assertEquals(feature_set.features_count, 37)
        self.assertEquals(feature_set.target_variable, 'hire_outcome')

        # named features type "str_to_timezone" should be added
        ftype = NamedFeatureType.query.filter_by(name='str_to_timezone')[0]
        self.assertTrue(ftype, 'Named type not added')
        self.assertEquals(ftype.type, 'composite')
        self.assertEquals(ftype.params, {u'chain': [{
            u'params': {u'pattern': u'UTC([-\\+]+\\d\\d).*'},
            u'type': u'regex'},
            {u'type': u'int'}]})

        # Checking features
        features = Feature.query.filter_by(feature_set=feature_set)
        self.assertEquals(features.count(), 37)

        def _check_feature(name, fields):
            feature = Feature.query.filter_by(
                name=name, feature_set=feature_set).one()
            for field, val in fields.iteritems():
                feature_value = getattr(feature, field)
                self.assertEquals(
                    feature_value, val,
                    'Field: %s: %s != %s' % (field, feature_value, val))
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
        transformer = feature.transformer
        self.assertTrue(feature.transformer)
        self.assertEquals(transformer['type'], 'Tfidf')
        self.assertEquals(
            transformer, {'ngram_range_max': 1,
                          'ngram_range_min': 1,
                          'min_df': 10,
                          'type': 'Tfidf'})

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

    # def test_import_export(self):
    #     """
    #     Import, than export to JSON should give same result.
    #     """
    #     # TODO:
    #     self.maxDiff = None
    #     content = open('./conf/features.json', 'r').read()
    #     features_json = json.loads(content)
    #     feature_set = FeatureSet.\
    #         from_model_features_dict("Set", features_json)
    #     features_dict = feature_set.to_dict()
    #     feature_set2 = FeatureSet.\
    #         from_model_features_dict("Set", features_dict)
    #     self.assertEquals(feature_set.to_dict(), feature_set2.to_dict())


def fields_from_dict(obj, fields):
    for key, val in fields.iteritems():
        setattr(obj, key, val)
