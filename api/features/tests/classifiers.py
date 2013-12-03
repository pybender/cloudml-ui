import logging
import json
# from bson import ObjectId

# from utils import FeaturePredefinedItems
# from api.views import ClassifierResource
# from api import app
# from api.models import Classifier
# from utils import BaseTestCase, MODEL_ID
# CLASSIFIER_ID = '519318e6106a6c0df349bc0b'
from api.base.test_utils import BaseDbTestCase
from utils import FeaturePredefinedItemsTestMixin, FeatureItemsTestMixin
from ..views import ClassifierResource
from ..models import PredefinedClassifier
from ..fixtures import PredefinedClassifierData


class TestClassifierDoc(BaseDbTestCase):
    """
    Tests for the Classifier document methods.
    """
    FIXTURES = ('classifiers.json', 'models.json')

    def test_to_dict(self):
        classifier = PredefinedClassifier.query.all()[0]
        self.assertEquals(classifier.to_dict(),
                          {"penalty": "l2", "type": "logistic regression"})

    def test_from_features(self):
        features = json.loads(open('./conf/features.json', 'r').read())
        classifier = Classifier.from_model_features_dict("Set", features)
        self.assertTrue(classifier, 'Classifier not set')
        self.assertEquals(classifier.name, 'Set')
        self.assertEquals(classifier.type, 'logistic regression')
        self.assertEquals(classifier.params, {"penalty": "l2"})


class PredefinedClassifiersTests(FeaturePredefinedItemsTestMixin):
    """
    Tests of the Classifiers API.
    """
    FIXTURES = ('classifiers.json', 'models.json')
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

    ### Predefined items tests goes here ###
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
            logging.debug("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

        data = {"name": "classifier name is here",
                'type': 'invalid'}
        _check(data, errors={
            'type': 'should be one of stochastic gradient descent classifier, \
support vector regression, logistic regression'})

        data['type'] = 'logistic regression'
        data["params"] = 'hello!'
        _check(data, errors={'params': 'invalid json: hello!'})

        classifier = self.obj
        data = {'name': classifier.name,
                'type': 'logistic regression'}
        _check(data, errors={
            'fields': 'name of predefined item should be unique'})

    def test_edit(self):
        self._test_edit()

    def test_delete_predefined_transformer(self):
        self.check_delete()


class ModelClassifierTest(BaseDbTestCase):
    ### Manipulating with model's classifier is here ###

    def test_post_validation(self):
        def _check(data, errors):
            """
            Checks validation errors
            """
            logging.debug("Checking validation with data %s", data)
            self.check_edit_error(data, errors)

        data = {"name": "classifier name is here",
                'type': 'invalid'}
        _check(data, errors={
            'type': 'should be one of stochastic gradient descent classifier, \
support vector regression, logistic regression'})

        data['type'] = 'logistic regression'
        data["params"] = 'hello!'
        _check(data, errors={'params': 'invalid json: hello!'})

        data = {'name': 'classifier#1',
                'type': 'logistic regression',
                'model_id': '512123b1106a6c5bcbc12efb'}
        _check(data, errors={u'model_id': u'Document not found'})

        data['predefined_selected'] = 'true'
        data['model_id'] = MODEL_ID
        _check(data, errors={u'classifier': u'classifier is required'})

        classifier = self.db.Classifier.find_one()
        data = {'name': classifier.name,
                'type': 'logistic regression'}
        _check(data, errors={
            'fields': 'name of predefined item should be unique'})

    def test_edit_model_classifier(self):
        data = {'name': 'new classifier name',
                'type': 'logistic regression',
                'params': '{"C": 1}',
                'model_id': MODEL_ID}

        self._check_put(data)
        model = self.db.Model.get_from_id(ObjectId(MODEL_ID))
        self.assertEqual(model.classifier['name'], data['name'])
        self.assertEqual(model.classifier['type'], data['type'])
        self.assertEqual(model.classifier['params'],
                         json.loads(data['params']))

    def test_edit_feature_transformer_from_predefined(self):
        classifier = self.db.Classifier.find_one()
        data = {'classifier': str(classifier._id),
                'model_id': MODEL_ID,
                'predefined_selected': 'true'}
        self._check_put(data, load_model=False)
        model = self.db.Model.get_from_id(ObjectId(MODEL_ID))
        self.assertEqual(model.classifier['name'], classifier.name)
        self.assertEqual(model.classifier['type'], classifier.type)
        self.assertEqual(model.classifier['params'], classifier.params)
