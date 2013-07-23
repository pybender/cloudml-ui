import httplib
import json

from utils import MODEL_ID, BaseTestCase
from bson.objectid import ObjectId
from api.utils import ERR_INVALID_DATA


class ModelTests(BaseTestCase):
    """
    Tests of the Models API.
    """
    MODEL_NAME = 'TrainedModel'
    FIXTURES = ('importhandlers.json', 'models.json', 'tests.json', 'examples.json', 'datasets.json',
                'weights.json', 'instances.json', )
    BASE_URL = '/cloudml/models/'

    def setUp(self):
        super(ModelTests, self).setUp()
        self.model = self.db.Model.find_one({'name': self.MODEL_NAME})

    def test_list(self):
        resp = self.app.get(self.BASE_URL)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('models' in data, data)
        models_resp = data['models']
        count = self.db.Model.find().count()
        self.assertEquals(count, len(data['models']))
        self.assertEquals(models_resp[0].keys(), [u'_id', u'name'])

        url = self._get_url(show='created_on,updated_on')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        models_resp = data['models']
        self.assertEquals(models_resp[0].keys(),
                          [u'updated_on', u'created_on', u'_id'])

    def test_filter(self):
        url = self._get_url(status='New')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        count = self.db.Model.find({'status': 'New'}).count()
        self.assertEquals(count, len(data['models']))

        url = self._get_url(name='Test')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        count = self.db.Model.find().count()
        self.assertEquals(count, len(data['models']), 'No name \
filter - all models should be returned')

    def test_comparable_filter(self):
        def _check(comparable):
            url = self._get_url(comparable=int(comparable))
            resp = self.app.get(url)
            self.assertEquals(resp.status_code, httplib.OK)
            data = json.loads(resp.data)
            count = self.db.Model.find({'comparable': comparable}).count()
            self.assertEquals(count, len(data['models']))

        _check(True)
        _check(False)

    def test_details(self):
        url = self._get_url(id=self.model._id)
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('model' in data, data)
        model_resp = data['model']
        self.assertEquals(str(self.model._id), model_resp['_id'])
        self.assertEquals(self.model.name, model_resp['name'])

        url = self._get_url(id=self.model._id, show='created_on,labels')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        model_resp = data['model']
        self.assertEquals(model_resp.keys(),
                          [u'created_on', u'labels', u'_id'])
        self.assertEquals(self.model.labels, model_resp['labels'])

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
        uri = self.BASE_URL
        post_data = {'importhandler': 'smth'}
        self._checkValidationErrors(uri, post_data, 'name is required')

    def test_post_with_invalid_features(self):
        uri = self.BASE_URL
        hanlder = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': hanlder,
                     'train_import_handler_file': hanlder,
                     'name': 'new'}
        self._checkValidationErrors(uri, post_data, 'Either features, either \
pickled trained model is required for posting model')

        post_data = {'importhandler': hanlder, 'features': 'smth',
                     'name': 'new'}
        self._checkValidationErrors(uri, post_data, 'Invalid features: \
smth No JSON object could be decoded')

        post_data = {'importhandler': 'smth', 'features': '{"a": "1"}',
                     'name': 'new'}
        self._checkValidationErrors(uri, post_data, 'Invalid features: \
schema-name is missing')

    def test_post_with_invalid_trainer(self):
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/test/invalid_model.dat', 'r')
        post_data = {'importhandler': handler,
                     'trainer': trainer,
                     'name': 'new'}
        self._checkValidationErrors(self.BASE_URL, post_data,
                                    "Invalid trainer")

    def test_post_new_model(self, name='new'):
        count = self.db.Model.find().count()
        features = open('./conf/features.json', 'r').read()
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'features': features,
                     'name': name}
        resp = self.app.post(self.BASE_URL, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue('model' in resp.data)
        new_count = self.db.Model.find().count()
        self.assertEquals(count + 1, new_count)

    def test_post_trained_model(self):
        count = self.db.Model.find().count()
        name = 'new2'
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/test/model.dat', 'r')
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'trainer': trainer,
                     'name': name}
        resp = self.app.post(self.BASE_URL, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue('model' in resp.data, resp.data)
        new_count = self.db.Model.find().count()
        self.assertEquals(count + 1, new_count)

        model = self.db.Model.find_one({'name': name})
        self.assertEquals(model.name, name)
        self.assertTrue(model.fs.trainer)

    def test_edit_model(self):
        # TODO: Add validation to importhandlers
        data = {'name': 'new name',
                'example_id': 'some_id',
                'example_label': 'some_label', }
        resp = self.app.put(self._get_url(id=self.model._id), data=data)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        model = self.db.Model.find_one({'_id': ObjectId(self.model._id)})
        self.assertEquals(data['model']['_id'], str(model._id))
        self.assertEquals(data['model']['name'], str(model.name))
        self.assertEquals(model.example_id, 'some_id')
        self.assertEquals(model.example_label, 'some_label')

    def test_edit_model_name(self):
        data = {'name': 'new name %@#'}
        resp = self.app.put(self._get_url(id=self.model._id), data=data)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        model = self.db.Model.find_one(id=self.model._id)
        self.assertEquals(data['model']['name'], 'new name %@#')
        self.assertEquals(model.name, 'new name %@#')

    def test_train_model(self):
        self.assertTrue(self.model.status, "New")

        url = self._get_url(id=self.model._id, action='train')

        # Setting import handler for train
        handler = self.db.ImportHandler.find_one({'_id': ObjectId('5170dd3a106a6c1631000000')})
        self.assertTrue(handler, 'Invalid fixtures: import handlers')
        self.model.train_import_handler = handler
        self.model.save()
        inst = self.db.Instance.find_one({'_id': ObjectId('5170dd3a106a6c1631000000')})
        self.assertTrue(inst, 'Invalid fixtures: instances')

        data = {}
        resp = self.app.put(url, data=data)
        self.assertTrue(resp.status_code, httplib.BAD_REQUEST)
        self.assertTrue('One of spot_instance_type, aws_instance is required' in resp.data, resp.data)

        data = {'aws_instance': str(inst._id)}
        resp = self.app.put(url, data=data)
        self.assertTrue(resp.status_code, httplib.BAD_REQUEST)
        self.assertTrue('One of parameters, dataset is required' in resp.data,
                        resp.data)

        # Tests specifying dataset
        data['dataset'] = '5170dd3a106a6c1631000001'
        resp = self.app.put(url, data=data)
        self.assertTrue(resp.status_code, httplib.BAD_REQUEST)
        self.assertTrue('DataSet not found' in resp.data, resp.data)

        data['dataset'] = '5270dd3a106a6c1631000000'
        resp = self.app.put(url, data=data)
        self.assertTrue(resp.status_code, httplib.OK)
        model_resp = json.loads(resp.data)['model']
        self.assertEquals(model_resp["status"], "Queued")
        self.assertEquals(model_resp["name"], self.model.name)

        # Tests specifying loading data parameters
        data = {'aws_instance': str(inst._id),
                'start': '2012-12-03'}
        resp = self.app.put(url, data=data)
        self.assertTrue(resp.status_code, httplib.BAD_REQUEST)
        self.assertTrue('Parameters category, end are required' in resp.data, resp.data)

        data.update({'end': '2012-12-04',
                     'category': '1'})
        self.assertTrue(resp.status_code, httplib.OK)

    def test_retrain_model(self):
        model_filter_params = {'model_name': self.MODEL_NAME,
                               'model_id': MODEL_ID}
        self.assertEquals(self.model.status, "Trained")

        def check(Model, exist=True, msg=''):
            """
            Checks whether documents exist.
            """
            obj_list = Model.find(model_filter_params)
            self.assertEqual(bool(obj_list.count()), exist, msg)
            return obj_list

        check(self.db.Test)
        check(self.db.TestExample)
        check(self.db.Weight)
        check(self.db.WeightsCategory)

        url = self._get_url(id=self.model._id, action='train')
        data = {'start': '2012-12-03',
                'end': '2012-12-04',
                'category': 'smth',
                'aws_instance': '5170dd3a106a6c1631000000'}
        resp = self.app.put(url, data=data)
        self.assertTrue(str(self.model._id) in resp.data, resp.data)

        check(self.db.Test, exist=False,
              msg='Tests should be removed after retrain model')
        check(self.db.TestExample, exist=False,
              msg='Tests Examples should be removed after retrain model')

        # Checking weights
        tr_weights = self.model.get_trainer().get_weights()
        valid_count = len(tr_weights['positive']) + len(tr_weights['negative'])
        weights = self.db.Weight.find(model_filter_params)

        self.assertEquals(weights.count(), valid_count)
        categories = self.db.WeightsCategory.find(model_filter_params)
        self.assertEquals(categories.count(), 6)
        self.model = self.db.Model.find_one({'_id': self.model._id})
        self.assertEquals(self.model.status, 'Trained')

    def test_delete(self):
        url = self._get_url(id=self.model._id)
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)

        resp = self.app.delete(url)
        self.assertEquals(resp.status_code, 204)

        model = self.db.Model.find_one({'name': self.MODEL_NAME})
        self.assertEquals(model, None, model)

        # Check wheither tests and examples was deleted
        params = {'model_name': self.MODEL_NAME}
        tests = self.db.Test.find(params).count()
        self.assertFalse(tests, "%s tests was not deleted" % tests)
        other_examples = self.db.Test.find().count()
        self.assertTrue(other_examples, "All tests was deleted!")

        examples = self.db.TestExample.find(params).count()
        self.assertFalse(examples, "%s test examples was not \
deleted" % examples)
        other_examples = self.db.TestExample.find().count()
        self.assertTrue(other_examples, "All examples was deleted!")

    def _checkValidationErrors(self, uri, post_data, message,
                               code=ERR_INVALID_DATA,
                               status_code=httplib.BAD_REQUEST):
        resp = self.app.post(uri, data=post_data)
        self.assertEquals(resp.status_code, status_code)
        data = json.loads(resp.data)
        err_data = data['response']['error']
        self.assertEquals(err_data['code'], code)
        self.assertTrue(message in err_data['message'],
                        "Response message is: %s" % err_data['message'])
