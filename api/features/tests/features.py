""" Features and FeatureSet resources, models related unittests. """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import httplib
import logging

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, \
    HTTP_HEADERS, FEATURE_COUNT
from ..views import FeatureResource, FeatureSetResource
from ..models import Feature, FeatureSet, NamedFeatureType
from ..fixtures import FeatureSetData, FeatureData, FEATURES_JSON
from api.ml_models.models import Model, Transformer
from api.ml_models.fixtures import ModelData, TransformerData
from api.base.models import db


class TestFeatureResource(BaseDbTestCase, TestChecksMixin):
    """
    Features API methods tests.
    """
    BASE_URL = '/cloudml/features/transformers/'
    RESOURCE = FeatureResource
    Model = Feature
    datasets = (FeatureSetData, FeatureData, ModelData,
                TransformerData)

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
            logging.info("Checking validation with data %s", data)
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
        }
        _check(data, errors={
            'transformer': "transformer-type: type is invalid"})

        data['transformer-params'] = 'aaa'
        _check(data, errors={
            'transformer': "transformer-params: JSON file is corrupted. \
Can not load it: aaa, transformer-type: type is invalid"})

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
        self.assertFalse(data["name"] in self.model.features)
        resp, obj = self.check_edit(data)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.feature_set_id, data['feature_set_id'])
        self.assertTrue(obj.required)
        self.assertTrue(obj.is_target_variable)
        self.assertEquals(obj.input_format, data['input_format'])
        self.assertEquals(obj.default, int(data['default']))
        model = Model.query.get(self.model.id)
        self.assertTrue(data["name"] in model.features,
                        "Features.json should be updated")

    def test_feature_with_named_type(self):
        named_type = NamedFeatureType(name='my_type', type='int')
        named_type.save()

        data = {
            "name": "contractor.tz",
            "type": named_type.name,
            "feature_set_id": self.model.features_set_id,
        }
        self.assertFalse(data["name"] in self.model.features)
        resp, obj = self.check_edit(data)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.feature_set_id, data['feature_set_id'])
        self.assertTrue(obj.required)
        model = Model.query.get(self.model.id)
        self.assertTrue(data["name"] in model.features,
                        "Features.json should be updated")

        data = {
            "name": "contractor.tz2",
            "type": "invalid named type",
            "feature_set_id": self.model.features_set_id,
        }
        self.check_edit_error(data, {'type': 'type is required'})

    def test_add_feature(self):
        """
        Adding feature with transformer and scaler
        """
        data = {
            "name": "jobpost title",
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

        transformer = Transformer.query.all()[0]
        data = {
            "name": "feature-with-pretrained-transformer",
            "type": "text",
            "feature_set_id": self.model.features_set_id,
            "transformer-transformer": transformer.id,
            "transformer-predefined_selected": 'true'
        }
        resp, obj = self.check_edit(data)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.type, data['type'])
        self.assertEquals(obj.feature_set_id, data['feature_set_id'])

        self.assertTrue(obj.transformer, "Transformer not added to feature")
        self.assertEquals(obj.transformer['type'], transformer.name)

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
                         "Transformer should be rem (%s)" % obj.transformer)
        self.assertFalse(obj.scaler, "scaler should be removed")

    def test_modify_locked_feature(self):
        self.model.features_set.locked = True
        self.model.features_set.save()
        data = {"type": "boolean"}
        url = self._get_url(id=self.obj.id, method='put')
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('The model referring to this', resp.data)

        url = self._get_url(id=self.obj.id, method='delete')
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('The model referring to this', resp.data)

    def test_make_target_variable(self):
        fset = self.model.features_set

        # TODO: Fix this hack. use refs in fixtures
        Feature.query.update(dict(feature_set_id=fset.id))

        data = {'is_target_variable': 'true', 'required': 'false',
                'disabled': 'true'}
        params = {'is_target_variable': False,
                  'feature_set_id': str(fset.id)}
        feature = Feature.query.filter_by(**params)[0]
        resp, feature = self.check_edit(data, id=feature.id)

        fset = FeatureSet.query.get(fset.id)
        self.assertEquals(feature.name, fset.target_variable)

        logging.debug('Target varialble is %s', feature.name)
        feature = Feature.query.get(feature.id)
        self.assertTrue(feature.is_target_variable)
        self.assertTrue(feature.required)
        self.assertFalse(feature.disabled)

        features = Feature.query.filter_by(**params)
        self.assertTrue(features.count())
        for f in features:
            self.assertFalse(f.is_target_variable)

        # check setting target variable to false when no other target variable
        # in features set
        resp, feature = self.check_edit(data, id=feature.id)
        data = {'is_target_variable': 'false'}
        url = self._get_url(id=feature.id, method='put')
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEqual(400, resp.status_code)
        self.assertIn('Target variable is not set', resp.data)

        # check deleting target variable
        url = self._get_url(id=feature.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('Target variable can not be deleted', resp.data)


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
                fset, ['target_variable', 'features_count', 'features_dict'])

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
        self.assertEquals(len(fset.features_dict['features']), 0)
        # Note: features_dict updates after accessing to features property
        print fset.features
        expire_fset()
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
        print fset.features
        expire_fset()
        self.assertEquals(len(fset.features_dict['features']), 2)

        feature1 = Feature.query.get(feature1.id)
        feature1.name = 'feature_new_name'
        feature1.save()

        print fset.features
        expire_fset()
        self.assertEquals(fset.features_count, 2)
        self.assertEquals(len(fset.features_dict['features']), 2)
        self.assertTrue(
            'feature_new_name' in str(fset.features_dict['features']))

        feature1 = Feature.query.get(feature1.id)
        feature1.delete()
        fset = FeatureSet.query.get(fset.id)
        print fset.features
        expire_fset()
        self.assertEquals(fset.features_count, 1)
        self.assertEquals(len(fset.features_dict['features']), 1)
        self.assertEquals(fset.features_dict['features'][0]['name'],
                          'hire_outcome')

    def test_load_from_features_dict(self):
        feature_set = FeatureSet()
        feature_set.from_dict(FEATURES_JSON)
        self.assertTrue(feature_set)
        self.assertEquals(feature_set.schema_name, 'bestmatch')
        self.assertEquals(len(feature_set.features['features']),
                          FEATURE_COUNT)
        self.assertEquals(feature_set.features_count, FEATURE_COUNT)
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
        self.assertEquals(features.count(), 35)

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
            transformer, {'type': 'Tfidf',
                          'params': {'ngram_range_max': 1,
                                     'ngram_range_min': 1,
                                     'min_df': 10}
                          })

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
    def test_field_type_to_feature_type(self):
        self.assertEqual('float', Feature.field_type_to_feature_type('float'))
        self.assertEqual(
            'boolean', Feature.field_type_to_feature_type('boolean'))
        self.assertEqual('int', Feature.field_type_to_feature_type('integer'))
        self.assertEqual('map', Feature.field_type_to_feature_type('json'))
        self.assertEqual('text', Feature.field_type_to_feature_type('string'))
        self.assertEqual('text', Feature.field_type_to_feature_type('blabla'))


class TestFeatureSetResource(BaseDbTestCase, TestChecksMixin):
    """
    Features API methods tests.
    """
    BASE_URL = '/cloudml/features/sets/'
    RESOURCE = FeatureSetResource
    Model = FeatureSet
    datasets = (FeatureSetData, FeatureData, ModelData,
                TransformerData)

    def setUp(self):
        BaseDbTestCase.setUp(self)
        self.model = Model.query.filter_by(name=ModelData.model_01.name)[0]
        self.obj = FeatureSet.query.filter_by(
            schema_name=FeatureSetData.bestmatch.schema_name)[0]
        self.model.features_set = self.obj
        self.model.save()

    def test_edit_group_by(self):
        # setting a group by field
        feature = Feature.query.filter_by(
            feature_set=self.obj,
            name='title').first()
        data = {"group_by": json.dumps(
            [{'id': feature.id,
             'text': feature.name}])}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertItemsEqual(obj.group_by, [feature])

        # removing group by field
        data = {"group_by": json.dumps([])}
        resp, obj = self.check_edit(data, id=self.obj.id)
        self.assertFalse(obj.group_by)

    def test_edit_locked(self):
        self.model.features_set.locked = True
        self.model.features_set.save()
        data = {"schema_name": "new name"}
        url = self._get_url(id=self.model.features_set.id, method='put')
        resp = self.client.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('The model referring to this', resp.data)

    def test_delete(self):
        feature_set = FeatureSet.query.filter_by(
            schema_name=FeatureSetData.bestmatch_01.schema_name).one()
        feature_set_id = feature_set.id
        url = self._get_url(id=feature_set.id, method='delete')
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEqual(204, resp.status_code)
        self.assertEqual(0, Feature.query.filter_by(
            feature_set_id=feature_set_id).count())
        self.assertEqual(0, FeatureSet.query.filter_by(
            id=feature_set_id).count())


def fields_from_dict(obj, fields):
    for key, val in fields.iteritems():
        setattr(obj, key, val)
