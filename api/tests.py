import unittest
import os
import json
import httplib

from api.serialization import encode_model
from api import app
from api.utils import ERR_INVALID_DATA


class BaseTestCase(unittest.TestCase):
    FIXTURES = []
    _LOADED_COLLECTIONS = []

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.fixtures_load()

    def tearDown(self):
        self.fixtures_cleanup()

    @property
    def db(self):
        return app.db

    def fixtures_load(self):
        for fixture in self.FIXTURES:
            data = self._load_fixture_data(fixture)
            for collection_name, documents in data.iteritems():
                self._LOADED_COLLECTIONS.append(collection_name)
                collection = self._get_collection(collection_name)
                collection.insert(documents)

    def fixtures_cleanup(self):
        for collection_name in self._LOADED_COLLECTIONS:
            collection = self._get_collection(collection_name)
            collection.remove()

    def _load_fixture_data(self, filename):
        filename = os.path.join('./api/fixtures/', filename)
        content = open(filename, 'rb').read()
        return json.loads(content)

    def _get_collection(self, name):
        callable_model = getattr(self.db, name)
        return callable_model.collection


class ModelTests(BaseTestCase):
    """
    Tests of the Models API.
    """
    MODEL_NAME = 'TrainedModel'
    FIXTURES = ('models.json', 'tests.json', 'examples.json')

    def test_list(self):
        resp = self.app.get('/cloudml/model/')
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('models' in data, data)
        models_resp = data['models']
        count = app.db.Model.find().count()
        self.assertEquals(count, len(data['models']))
        self.assertEquals(models_resp[0].keys(), [u'_id', u'name'])

        resp = self.app.get('/cloudml/model/?show=created_on,updated_on')
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        models_resp = data['models']
        self.assertEquals(models_resp[0].keys(),
                          [u'updated_on', u'created_on', u'_id'])

    def test_filter(self):
        resp = self.app.get('/cloudml/model/?status=New')
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        count = app.db.Model.find({'status': 'New'}).count()
        self.assertEquals(count, len(data['models']))

        resp = self.app.get('/cloudml/model/?name=Test')
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        count = app.db.Model.find().count()
        self.assertEquals(count, len(data['models']), 'No name \
filter - all models should be returned')

    def test_comparable_filter(self):
        def _check(comparable):
            resp = self.app.get('/cloudml/model/?comparable=%d' % comparable)
            self.assertEquals(resp.status_code, httplib.OK)
            data = json.loads(resp.data)
            count = app.db.Model.find({'comparable': comparable}).count()
            self.assertEquals(count, len(data['models']))

        _check(True)
        _check(False)

    def test_details(self):
        model = app.db.Model.find_one({'name': self.MODEL_NAME})
        resp = self.app.get('/cloudml/model/%s' % self.MODEL_NAME)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('model' in data, data)
        model_resp = data['model']
        self.assertEquals(str(model._id), model_resp['_id'])
        self.assertEquals(model.name, model_resp['name'])

        resp = self.app.get('/cloudml/model/%s?show=created_on,labels' %
                            self.MODEL_NAME)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        model_resp = data['model']
        self.assertEquals(model_resp.keys(),
                          [u'created_on', u'labels', u'_id'])
        self.assertEquals(model.labels, model_resp['labels'])

    def test_weights(self):
        # TODO: Add weights to fixtures and implement test
        pass

    def test_download(self):
        def check(field, is_invalid=False):
            url = '/cloudml/model/%s/download?field=%s' % (self.MODEL_NAME, field)
            resp = self.app.get(url)
            if not is_invalid:
                self.assertEquals(resp.status_code, httplib.OK)
                self.assertEquals(resp.mimetype, 'text/plain')
                self.assertEquals(resp.headers['Content-Disposition'],
                                  'attachment; filename=%s-%s.json' % \
                                    (self.MODEL_NAME, field))
            else:
                self.assertEquals(resp.status_code, 400)
        check('importhandler')
        check('features')
        check('train_importhandler')
        check('invalid', is_invalid=True)

    def test_post_with_invalid_features(self):
        uri = '/cloudml/model/new'
        post_data = {'importhandler': 'smth'}
        self._checkValidationErrors(uri, post_data, 'Either features, either \
pickled trained model is required')

        post_data = {'importhandler': 'smth', 'features': 'smth'}
        self._checkValidationErrors(uri, post_data, 'Invalid features: \
smth No JSON object could be decoded ')

        post_data = {'importhandler': 'smth', 'features': '{}'}
        self._checkValidationErrors(uri, post_data, 'Invalid features: \
schema-name is missing')

    def test_post_with_invalid_import_handler(self):
        uri = '/cloudml/model/new'
        self._checkValidationErrors(uri, {}, 'importhandler is required in \
values')

        features = open('./conf/features.json', 'r').read()
        post_data = {'importhandler': 'smth',
                     'features': features}
        self._checkValidationErrors(uri, post_data, 'Invalid Import Handler: \
No JSON object could be decoded')

        features = open('./conf/features.json', 'r').read()
        post_data = {'importhandler': '{}',
                     'features': features}
        self._checkValidationErrors(uri, post_data, 'Invalid Import Handler: \
No target schema defined in config')

    def test_post_with_invalid_trainer(self):
        uri = '/cloudml/model/new'
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/fixtures/invalid_model.dat', 'r')
        post_data = {'importhandler': handler,
                     'trainer': trainer}
        self._checkValidationErrors(uri, post_data, 'Invalid trainer: Could \
not unpickle trainer - could not find MARK')

        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/fixtures/invalid_testmodel.dat', 'r')
        post_data = {'importhandler': handler,
                     'trainer': trainer}
        self._checkValidationErrors(uri, post_data, "Invalid trainer: Could \
not unpickle trainer - 'module' object has no attribute 'apply_mappings'")

    def test_post_new_model(self):
        count = app.db.Model.find().count()
        name = 'UnitTestModel1'
        features = open('./conf/features.json', 'r').read()
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'importhandler': handler,
                     'features': features}
        resp = self.app.post('/cloudml/model/%s' % name, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue('model' in resp.data)
        new_count = app.db.Model.find().count()
        self.assertEquals(count + 1, new_count)

    def test_post_trained_model(self):
        count = app.db.Model.find().count()
        name = 'UnitTestModel2'
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./model.dat', 'r')
        post_data = {'importhandler': handler,
                     'trainer': trainer}
        resp = self.app.post('/cloudml/model/%s' % name, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue('model' in resp.data)
        new_count = app.db.Model.find().count()
        self.assertEquals(count + 1, new_count)

        # Checking weights and weights categories filling
        opening = app.db.WeightsCategory.find_one({'model_name': name,
                                                   'name': 'opening'})
        self.assertEquals(opening['parent'], '')
        self.assertEquals(opening['short_name'], 'opening')
        self.assertEquals(opening['model_name'], name)

        opening_type = app.db.WeightsCategory.find_one(
            {'model_name': name, 'name': 'opening.type'})
        self.assertEquals(opening_type['parent'], 'opening')
        self.assertEquals(opening_type['short_name'], 'type')
        self.assertEquals(opening_type['model_name'], name)

        # customer = app.db.Weight.find_one({'model_name': name,
        #                                    'name': 'opening->title->customer'})
        # self.assertEquals(customer['is_positive'], True)
        # self.assertEquals(customer['css_class'], 'green darker')
        # self.assertEquals(customer['value'], 2.0388470724264844)
        # self.assertEquals(customer['model_name'], name)

        # authorize = app.db.Weight.find_one({'model_name': name,
        #                                     'name': 'opening->skills->authorize.net'})
        # self.assertEquals(authorize['parent'], 'opening->skills')
        # self.assertEquals(authorize['is_positive'], False)
        # self.assertEquals(authorize['short_name'], 'authorize.net')
        # self.assertEquals(authorize['css_class'], 'red lightest')
        # self.assertEquals(authorize['value'], 0)
        # self.assertEquals(authorize['model_name'], name)

        model = app.db.Model.find_one({'name': name})
        self.assertEquals(model.name, name)
        self.assertTrue(model.fs.trainer)

    def test_delete(self):
        url = '/cloudml/model/' + self.MODEL_NAME
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)

        resp = self.app.delete(url)
        self.assertEquals(resp.status_code, 204)

        model = app.db.Model.find_one({'name': self.MODEL_NAME})
        self.assertEquals(model, None, model)

        # Check wheither tests and examples was deleted
        params = {'model_name': self.MODEL_NAME}
        tests = app.db.Test.find(params).count()
        self.assertFalse(tests, "%s tests was not deleted" % tests)
        other_examples = app.db.Test.find().count()
        self.assertTrue(other_examples, "All tests was deleted!")

        examples = app.db.TestExample.find(params).count()
        self.assertFalse(examples, "%s test examples was not \
deleted" % examples)
        other_examples = app.db.TestExample.find().count()
        self.assertTrue(other_examples, "All examples was deleted!")

    def _checkValidationErrors(self, uri, post_data, message,
                               code=ERR_INVALID_DATA,
                               status_code=httplib.BAD_REQUEST):
        resp = self.app.post(uri, data=post_data)
        self.assertEquals(resp.status_code, status_code)
        data = json.loads(resp.data)
        err_data = data['response']['error']
        self.assertEquals(err_data['code'], code)
        self.assertEquals(err_data['message'], message)


class TestTests(BaseTestCase):
    MODEL_NAME = 'TrainedModel'
    TEST_NAME = 'Test-1'
    FIXTURES = ('models.json', 'tests.json', 'examples.json')

    def test_list(self):
        url = self._get_url(self.MODEL_NAME, search='show=name,status')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('tests' in data)
        tests = app.db.Test.find({'model_name': self.MODEL_NAME})
        count = tests.count()
        self.assertEquals(count, len(data['tests']))
        self.assertTrue(tests[0].name in resp.data, resp.data)
        self.assertTrue(tests[0].status in resp.data, resp.data)
        self.assertFalse(tests[0].model_name in resp.data, resp.data)

    def test_details(self):
        url = self._get_url(self.MODEL_NAME, self.TEST_NAME,
                            'show=name,status')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('test' in data, data)
        test_data = data['test']
        test = app.db.Test.find_one({'model_name': self.MODEL_NAME,
                                     'name': self.TEST_NAME})
        self.assertEquals(test.name, test_data['name'], resp.data)
        self.assertEquals(test.status, test_data['status'], resp.data)
        self.assertFalse('model_name' in test_data, test_data)

    # def test_post(self):
    #     url = self._get_url(self.MODEL_NAME)
    #     resp = self.app.post(url)
    #     self.assertEquals(resp.status_code, httplib.OK)

    def test_delete(self):
        url = self._get_url(self.MODEL_NAME, self.TEST_NAME,
                            'show=name,status')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)

        resp = self.app.delete(url)
        self.assertEquals(resp.status_code, 204)
        params = {'model_name': self.MODEL_NAME,
                  'name': self.TEST_NAME}
        test = app.db.Test.find_one(params)
        self.assertEquals(test, None, test)

        params = {'model_name': self.MODEL_NAME,
                  'test_name': self.TEST_NAME}
        examples = app.db.TestExample.find(params).count()
        self.assertFalse(examples, "%s test examples was not \
deleted" % examples)
        other_examples = app.db.TestExample.find().count()
        self.assertTrue(other_examples, "All examples was deleted!")

    def _get_url(self, model, test=None, search=None):
        if test:
            return '/cloudml/model/%s/test/%s?%s' % (model, test, search)
        else:
            return '/cloudml/model/%s/tests?%s' % (model, search)


def dumpdata(document_list, fixture_name):
    content = json.dumps(document_list, default=encode_model)
    file_path = os.path.join('./api/fixtures/', fixture_name)
    with open(file_path, 'w') as ffile:
        ffile.write(content)
