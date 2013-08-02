import httplib
import json
from mock import patch

from utils import MODEL_ID, BaseTestCase, FEATURE_COUNT, TARGET_VARIABLE
from bson.objectid import ObjectId
from api.utils import ERR_INVALID_DATA
from api.views import Models as ModelsResource


class ModelTests(BaseTestCase):
    """
    Tests of the Models API.
    """
    INSTANCE_ID = '5170dd3a106a6c1631000000'
    MODEL_NAME = 'TrainedModel'
    RELATED_PARAMS = {'model_id': MODEL_ID, 'model_name': MODEL_NAME}
    FIXTURES = ('importhandlers.json', 'models.json',
                'tests.json', 'examples.json', 'datasets.json',
                'weights.json', 'instances.json', )
    RESOURCE = ModelsResource
    BASE_URL = '/cloudml/models/'

    def setUp(self):
        super(ModelTests, self).setUp()
        self.Model = self.db.Model
        self.obj = self.model = self.db.Model.find_one({
            '_id': ObjectId(MODEL_ID)})

    def test_list(self):
        self._check_list(show='')
        self._check_list(show='created_on,updated_on')

    def test_filter(self):
        self._check_filter({'status': 'New'})
        # No name filter - all models should be returned
        self._check_filter({'name': 'Test'}, {})

        # Comparable filter
        self._check_filter({'comparable': 1}, {'comparable': True})
        self._check_filter({'comparable': 0}, {'comparable': False})

    def test_details(self):
        self._check_details(show='')
        self._check_details(show='created_on,labels')

    def test_download(self):
        def check(field, is_invalid=False):
            url = self._get_url(id=self.model._id, action='download',
                                field=field)
            resp = self.app.get(url)
            if not is_invalid:
                self.assertEquals(resp.status_code, httplib.OK)
                self.assertEquals(resp.mimetype, 'text/plain')
                self.assertEquals(resp.headers['Content-Disposition'],
                                  'attachment; filename=%s-%s.json' %
                                  (self.MODEL_NAME, field))
            else:
                self.assertEquals(resp.status_code, 400)
        check('features')
        check('invalid', is_invalid=True)

    def test_post_without_name(self):
        self._check_post({'importhandler': 'smth'},
                         error='name is required')

    def test_post_with_invalid_features(self):
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'name': 'new'}
        self._check_post(post_data, error='Either features, either \
pickled trained model is required for posting model')

        post_data = {'importhandler': handler,
                     'features': 'smth',
                     'name': 'new'}
        self._check_post(post_data, error='Invalid features: \
smth No JSON object could be decoded')

        post_data = {'importhandler': 'smth',
                     'features': '{"a": "1"}',
                     'name': 'new'}
        self._check_post(post_data, error='Invalid features: \
schema-name is missing')

    def test_post_with_invalid_trainer(self):
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/fixtures/invalid_model.dat', 'r')
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'trainer': trainer,
                     'name': 'new'}
        self._check_post(post_data, error="Invalid trainer")

    def test_post_new_model(self, name='new'):
        #count = self.db.Model.find().count()
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'features': open('./conf/features.json', 'r').read(),
                     'name': name}
        resp, model = self._check_post(post_data, load_model=True)
        self.assertEquals(model.name, name)
        self.assertEquals(model.status, model.STATUS_NEW)
        self.assertTrue(model.test_import_handler,
                        "Test import handler was not set")
        self.assertTrue(model.train_import_handler,
                        "Train import handler was not set")
        self.assertTrue(model.features, "Features was not set")
        self.assertEquals(model.labels, [],
                          "Labels is empty for recently posted model")
        self.assertFalse(model.dataset)
        self.assertEquals(model.feature_count, FEATURE_COUNT)
        self.assertEquals(model.target_variable, TARGET_VARIABLE)
        self.assertFalse(model.example_id)
        self.assertFalse(model.example_label)
        self.assertFalse(model.comparable)
        self.assertEquals(model.tags, [])
        self.assertFalse(model.weights_synchronized)
        self.assertFalse(model.error)

    def test_post_trained_model(self):
        name = 'new2'
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/fixtures/model.dat', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'trainer': trainer,
                     'name': name}
        resp, model = self._check_post(post_data, load_model=True)
        self.assertEquals(model.name, name)
        self.assertEquals(model.status, model.STATUS_TRAINED)
        self.assertTrue(model.fs.trainer)

    def test_edit_model(self):
        # TODO: Add validation to importhandlers
        data = {'name': 'new name',
                'example_id': 'some_id',
                'example_label': 'some_label', }
        resp, model = self._check_put(data, load_model=True)
        data = json.loads(resp.data)
        self.assertEquals(data['model']['name'], str(model.name))
        self.assertEquals(model.example_id, 'some_id')
        self.assertEquals(model.example_label, 'some_label')

    def test_edit_model_name(self):
        data = {'name': 'new name %@#'}
        resp, model = self._check_put(data, load_model=True)
        data = json.loads(resp.data)
        self.assertTrue(model.name == data['model']['name'] ==
                        'new name %@#')

    def test_train_model_validation_errors(self):
        self.assertTrue(self.model.status, "New")
        self._check_put({}, action='train',
                        error='One of spot_instance_type, \
aws_instance is required')

        data = {'aws_instance': self.INSTANCE_ID,
                'start': '2012-12-03'}
        self._check_put(data, action='train',
                        error='Parameters category, end are required')

        data = {'aws_instance': self.INSTANCE_ID}
        self._check_put(data, action='train',
                        error='One of parameters, dataset is required')

        # Tests specifying dataset
        data['dataset'] = '000000000000000000000001'
        self._check_put(data, action='train',
                        error='DataSet not found')

    def test_train_model_with_dataset(self):
        # TODO: Check with dataset from another handler
        handler_id = str(self.obj.train_import_handler._id)
        ds = self.db.DataSet.find({
            'import_handler_id': handler_id})[0]
        data = {'aws_instance': self.INSTANCE_ID,
                'dataset': str(ds._id)}
        resp, model = self._check_put(data, action='train', load_model=True)
        model_resp = json.loads(resp.data)['model']
        self.assertEquals(model_resp["status"], "Queued")
        self.assertEquals(model_resp["name"], self.model.name)
        # NOTE: Make sure that ds.gz file exist in test_data folder
        self.assertEqual(model.status, model.STATUS_TRAINED, model.error)

        # TODO: check other fields of the model

    @patch('api.models.DataSet.save_to_s3')
    def test_train_model_with_load_params(self, save_to_s3_mock):
        data = {'aws_instance': self.INSTANCE_ID,
                'start': '2012-12-03',
                'end': '2012-12-04',
                'category': '1'}
        resp, model = self._check_put(data, action='train',
                                      load_model=True)
        model_resp = json.loads(resp.data)['model']
        self.assertEquals(model_resp["status"], "Queued")
        self.assertEquals(model_resp["name"], self.model.name)
        self.assertEqual(model.status, model.STATUS_TRAINED)

        # TODO: check other fields of the model

    @patch('api.models.DataSet.save_to_s3')
    def test_retrain_model(self, save_to_s3_mock):
        self.assertEquals(self.obj.status, "Trained")
        self.check_related_docs_existance(self.db.Test)
        self.check_related_docs_existance(self.db.TestExample)
        self.check_related_docs_existance(self.db.Weight)
        self.check_related_docs_existance(self.db.WeightsCategory)

        data = {'start': '2012-12-03',
                'end': '2012-12-04',
                'category': 'smth',
                'aws_instance': self.INSTANCE_ID}
        resp, model = self._check_put(data, action='train',
                                      load_model=True)
        self.assertEquals(model.status, model.STATUS_TRAINED)

        self.check_related_docs_existance(self.db.Test, exist=False,
                                          msg='Tests should be removed \
after retrain model')
        self.check_related_docs_existance(self.db.TestExample, exist=False,
                                          msg='Tests Examples should be \
removed after retrain model')

        # Checking weights
        self.assertTrue(model.weights_synchronized)
        tr_weights = self.model.get_trainer().get_weights()
        valid_count = len(tr_weights['positive']) + len(tr_weights['negative'])
        weights = self.db.Weight.find(self.RELATED_PARAMS)

        self.assertEquals(weights.count(), valid_count)
        categories = self.db.WeightsCategory.find(self.RELATED_PARAMS)
        self.assertEquals(categories.count(), 6)
        self.model = self.db.Model.find_one({'_id': self.model._id})
        self.assertEquals(self.model.status, 'Trained')

    def test_delete(self):
        self.check_related_docs_existance(self.db.Test)
        self.check_related_docs_existance(self.db.TestExample)

        self._check_delete()

        # Check wheither tests and examples was deleted
        self.check_related_docs_existance(self.db.Test, exist=False,
                                          msg='Tests should be removed \
when remove model')
        self.check_related_docs_existance(self.db.TestExample, exist=False,
                                          msg='Tests Examples should be \
when remove model')

        # Checks whether not all docs was deleted
        self.assertTrue(self.db.Test.find().count(),
                        "All tests was deleted!")
        self.assertTrue(self.db.TestExample.find().count(),
                        "All examples was deleted!")
