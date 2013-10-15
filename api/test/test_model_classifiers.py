from bson import ObjectId

from api.views import ClassifierResource
from utils import MODEL_ID, FeaturePredefinedItems, HTTP_HEADERS


class ClassifiersTests(FeaturePredefinedItems):
    """
    Tests for the Classifier document methods.
    """
    CLASSIFIER_ID = '519318e6106a6c0df489bc1a'
    FIXTURES = ('classifiers.json', 'models.json',)
    BASE_URL = '/cloudml/features/classifiers/'
    RESOURCE = ClassifierResource

    OBJECT_NAME = 'classifier'
    DATA = {'name': 'Test Classifier',
            'type': 'stochastic gradient descent classifier',
            'params': '{"loss":"test"}'}

    TARGET_ID_FIELD = 'model_id'

    def __init__(self, *args, **kwargs):
        super(ClassifiersTests, self).__init__(*args, **kwargs)
        self.TARGET_MODEL = self.db.Model

    def setUp(self):
        super(ClassifiersTests, self).setUp()
        self.Model = self.db.Classifier
        self.obj = self.Model.get_from_id(ObjectId(self.CLASSIFIER_ID))
        self.assertTrue(self.obj)
        self.model = self.db.Model.find_one()

    def test_list(self):
        self._check_list(show='name')

    def test_filter(self):
        self._check_filter({'is_predefined': 1}, {'is_predefined': True})

    def test_details(self):
        self._check_details()

    def test_add_predefined_classifier(self):
        self._test_add_predefined()

    def test_add_model_classifier(self):
        self._test_add_feature_item(self.model)

    def add_model_classifier_from_predefined(self):
        classifier = self.db.Classifier.find_one({'is_predefined': True})
        self._add_feature_item_from_predefined(self.model, classifier)

    def test_edit_predefined_classifier(self):
        self._test_edit_predefined_item()

    def test_edit_model_classifier(self):
        model = self.db.Model.get_from_id(ObjectId(MODEL_ID))
        self.assertTrue(model.classifier, "Invalid fixtures")
        data = {'name': 'new classifier name',
                'type': 'logistic regression',
                'params': '{"penalty": "l2"}'}

        resp, obj = self._test_edit_feature_item(model, extra_data=data)
        self.assertEqual(obj.params, {"penalty": "l2"})

    def test_edit_model_classifier_from_predefined(self):
        model = self.db.Model.get_from_id(ObjectId(MODEL_ID))
        self.assertTrue(model.classifier, "Invalid fixtures")

        classifier = self.db.Classifier.find_one({'is_predefined': True})
        self._edit_feature_item_from_predefined(model, classifier)

    def test_delete_predefined_classifier(self):
        self._check_delete()

    def test_delete_model_classifier(self):
        """
        Check that we can't delete model classifier
        """
        model = self.db.Model.get_from_id(ObjectId(MODEL_ID))
        self.assertTrue(model.classifier, "Invalid fixtures")
        self.assertFalse(model.classifier.is_predefined)

        url = self._get_url(id=model.classifier._id)
        resp = self.app.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 400)
