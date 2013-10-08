import httplib
import json
from bson import ObjectId

from api import app
from api.models import Classifier
from utils import MODEL_ID, BaseTestCase


class TestClassifierDoc(BaseTestCase):
    """
    Tests for the Classifier document methods.
    """
    FIXTURES = ('models.json', )

    def test_from_features(self):
        model = app.db.Model.get_from_id(ObjectId(MODEL_ID))

        classifier = Classifier.from_model_features_dict("Set", model.features)
        self.assertTrue(classifier, 'Classifier not set')
        self.assertEquals(classifier.name, 'Set')
        self.assertEquals(classifier.type, 'logistic regression')
        self.assertEquals(classifier.params, {"penalty": "l2"})
