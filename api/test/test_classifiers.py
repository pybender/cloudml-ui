import json
from bson import ObjectId

from api import app
from api.models import Classifier
from utils import BaseTestCase
CLASSIFIER_ID = '519318e6106a6c0df349bc0b'


class TestClassifierDoc(BaseTestCase):
    """
    Tests for the Classifier document methods.
    """
    FIXTURES = ('classifiers.json', 'models.json')

    def test_to_dict(self):
        classifier = app.db.Classifier.get_from_id(ObjectId(CLASSIFIER_ID))
        self.assertEquals(classifier.to_dict(),
                          {"penalty": "l2", "type": "logistic regression"})

    def test_from_features(self):
        features = json.loads(open('./conf/features.json', 'r').read())
        classifier = Classifier.from_model_features_dict("Set", features)
        self.assertTrue(classifier, 'Classifier not set')
        self.assertEquals(classifier.name, 'Set')
        self.assertEquals(classifier.type, 'logistic regression')
        self.assertEquals(classifier.params, {"penalty": "l2"})
