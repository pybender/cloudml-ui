""" Classifier resource, model related unittests. """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import httplib
import json

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from api.ml_models.fixtures import ModelData
from api.ml_models.models import Model, db
from utils import FeaturePredefinedItemsTestMixin
from ..views import ClassifierResource
from ..models import PredefinedClassifier
from ..fixtures import PredefinedClassifierData
from api.features.fixtures import FeatureSetData, FeatureData, FEATURES_JSON
from ..config import CLASSIFIERS


class TestClassifierDoc(BaseDbTestCase):
    """
    Tests for the Classifier document methods.
    """
    datasets = (PredefinedClassifierData, )

    def test_to_dict(self):
        classifier = PredefinedClassifier.query.filter_by(
            name=PredefinedClassifierData.lr_classifier.name).one()
        self.assertEquals(classifier.to_dict(),
                          {"params": {"penalty": "l2"},
                           "type": "logistic regression"})

    def test_from_features(self):
        classifier = PredefinedClassifier(name='Set')
        classifier.from_dict(FEATURES_JSON['classifier'])

        db.session.refresh(classifier)
        self.assertTrue(classifier, 'Classifier not set')
        self.assertEquals(classifier.name, 'Set')
        self.assertEquals(classifier.type, 'logistic regression')
        self.assertEquals(classifier.params, {"penalty": "l2"})


class PredefinedClassifiersTests(FeaturePredefinedItemsTestMixin):
    """
    Tests of the Classifiers API.
    """
    BASE_URL = '/cloudml/features/classifiers/'
    RESOURCE = ClassifierResource

    OBJECT_NAME = 'classifier'
    DATA = {'type': 'logistic regression',
            'name': 'My predef classifier',
            'params': "{}"}
    Model = PredefinedClassifier
    datasets = (PredefinedClassifierData, )

    def setUp(self):
        super(PredefinedClassifiersTests, self).setUp()
        self.obj = self.Model.query.all()[0]
        self.assertTrue(self.obj)

    # ==== Predefined items tests goes here ====
    def test_list(self):
        self.check_list(show='name,type')

    def test_details(self):
        self.check_details()

    def test_add(self):
        self._test_add()

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.info("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

        data = {"name": "classifier name is here",
                'type': 'invalid'}
        _check(data, errors={
            'type': 'Should be one of %s' % ', '.join(CLASSIFIERS.keys())})

        data['type'] = 'logistic regression'
        data["params"] = 'hello!'
        _check(data, errors={'params': "JSON file is corrupted. "
               "Can not load it: hello!"})

        classifier = self.obj
        data = {'name': classifier.name,
                'type': 'logistic regression'}
        _check(data, errors={
            'name': "Predefined classifier with same name already exist. "
            "Please choose another one."})

    def test_edit(self):
        self._test_edit()

    def test_delete_predefined_transformer(self):
        self.check_delete()


class ModelClassifierTest(BaseDbTestCase, TestChecksMixin):
    """ Manipulating with model's classifier is here """
    BASE_URL = '/cloudml/features/classifiers/'
    OBJECT_NAME = 'classifier'
    DATA = {'type': 'logistic regression',
            'name': 'My predef classifier',
            'params': "{}"}
    datasets = (FeatureData, FeatureSetData, ModelData,
                PredefinedClassifierData, )

    def test_post_predefined_classifier(self):
        name = "classifier name"
        data = {"name": name,
                'type': 'logistic regression',
                'params': json.dumps({
                    'C': '1.5',
                    'dual': 'True'
                })}
        resp = self._check(data=data, method='post')
        classifier = PredefinedClassifier.query.get(resp['classifier']['id'])
        self.assertEqual(classifier.type, data['type'])
        self.assertEqual(classifier.params['C'], 1.5)
        self.assertEqual(classifier.params['dual'], True)

    def test_classifier_parameters_types_convertion(self):
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        data = {"name": "classifier name",
                'type': 'logistic regression',
                'model_id': model.id,
                'params': json.dumps({
                    'C': '1.5',
                    'dual': 'True'
                })}
        self._check(data=data, method='post')
        model = Model.query.get(model.id)
        self.assertEqual(model.classifier['type'], data['type'])
        self.assertEqual(model.classifier['params']['C'], 1.5)
        self.assertEqual(model.classifier['params']['dual'], True)

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.info("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

        data = {"name": "classifier name is here",
                'type': 'logistic regression',
                'model_id': 1000}
        _check(data, errors={u'model_id': u'Document not found'})

        data['predefined_selected'] = 'true'
        data['model_id'] = Model.query.filter_by(
            name=ModelData.model_01.name).one().id
        _check(data, errors={u'classifier': u'classifier is required'})

    def test_post_deployed_model(self):
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        model.on_s3 = True
        model.save()
        data = {'name': 'new classifier name',
                'type': 'logistic regression',
                'params': '{"C": 1}',
                'model_id': model.id}
        resp = self.client.post(
            self.BASE_URL, data=data, headers=HTTP_HEADERS)
        self.assertEqual(405, resp.status_code)
        self.assertIn('Model is deployed', resp.data)

    def test_edit(self):
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.assertTrue(model)
        data = {'name': 'new classifier name',
                'type': 'logistic regression',
                'params': '{"C": 1}',
                'model_id': model.id}

        self._check(data=data, method='post')
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.assertEqual(model.classifier['type'], data['type'])
        self.assertEqual(model.classifier['params']['C'], 1)

    def test_edit_from_predefined(self):
        classifier = PredefinedClassifier.query.filter_by(
            name=PredefinedClassifierData.lr_classifier.name).one()
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        data = {'classifier': classifier.id,
                'model_id': model.id,
                'predefined_selected': 'true'}
        self._check(data=data, method='post')
        model = Model.query.filter_by(name=ModelData.model_01.name).one()
        self.assertEqual(model.classifier['type'], classifier.type)
        self.assertEqual(model.classifier['params']['penalty'], "l2")

    def check_edit_error(self, post_data, errors, **data):
        from api.base.resources import ERR_INVALID_DATA
        url = self._get_url(**data)
        resp = self.client.post(url, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        resp_data = json.loads(resp.data)
        err_data = resp_data['response']['error']
        self.assertEquals(err_data['code'], ERR_INVALID_DATA)
        self._check_errors(err_data, errors)
