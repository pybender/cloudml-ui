import json
from mock import patch
from bson.objectid import ObjectId

from utils import BaseTestCase
from utils import MODEL_ID
from api.views import Tests as TestResource


class TestTests(BaseTestCase):
    TEST_ID = '000000000000000000000002'
    MODEL_PARAMS = {'model_id': MODEL_ID}
    RELATED_PARAMS = {'test_id': TEST_ID, 'model_id': MODEL_ID}
    RESOURCE = TestResource
    FIXTURES = ('importhandlers.json', 'models.json', 'tests.json',
                'examples.json', 'instances.json', )

    def setUp(self):
        super(TestTests, self).setUp()
        self.model = self.db.Model.find_one({'_id': ObjectId(MODEL_ID)})
        self.assertTrue(self.model, 'Invalid fixtures: models')

        self.Model = self.db.Test
        self.obj = self.db.Test.find_one({
            '_id': ObjectId(self.TEST_ID)})
        self.assertTrue(self.obj, 'Invalid fixtures: tests')

        self.BASE_URL = '/cloudml/models/%s/tests/' % self.model._id

    def test_list(self):
        self._check_list(show='', query_params=self.MODEL_PARAMS)
        self._check_list(show='name,status', query_params=self.MODEL_PARAMS)

    def test_details(self):
        self._check_details(show='name,status')

    @patch('api.models.DataSet.save_to_s3')
    def test_post(self, save_to_s3_mock):
        data = {'start': '2012-12-03',
                'end': '2012-12-04',
                'category': 'smth',
                'aws_instance': '5170dd3a106a6c1631000000'}
        resp, test = self._check_post(data, load_model=True)
        test_resp = json.loads(resp.data)['test']

        # TODO: Why status is imported, not completed here?
        #self.assertEquals(test.status, test.STATUS_COMPLETED)
        # TODO: check resp and created test

    def test_post_with_dataset(self):
        # TODO: check post with spec. dataset
        pass

    def test_recalc_confusion_matrix(self):
        # TODO:
        pass

    def test_delete(self):
        self.check_related_docs_existance(self.db.TestExample)
        self._check_delete()

        self.check_related_docs_existance(self.db.TestExample, exist=False,
                                          msg='Tests Examples should be \
when remove test')

        # Checks whether not all docs was deleted
        self.assertTrue(self.db.Test.find().count(),
                        "All tests was deleted!")
        self.assertTrue(self.db.TestExample.find().count(),
                        "All examples was deleted!")
