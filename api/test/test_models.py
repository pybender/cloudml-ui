import httplib
import json

from utils import BaseTestCase
from api.utils import ERR_INVALID_DATA


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
        count = self.db.Model.find().count()
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
        count = self.db.Model.find({'status': 'New'}).count()
        self.assertEquals(count, len(data['models']))

        resp = self.app.get('/cloudml/model/?name=Test')
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        count = self.db.Model.find().count()
        self.assertEquals(count, len(data['models']), 'No name \
filter - all models should be returned')

    def test_comparable_filter(self):
        def _check(comparable):
            resp = self.app.get('/cloudml/model/?comparable=%d' % comparable)
            self.assertEquals(resp.status_code, httplib.OK)
            data = json.loads(resp.data)
            count = self.db.Model.find({'comparable': comparable}).count()
            self.assertEquals(count, len(data['models']))

        _check(True)
        _check(False)

    def test_details(self):
        model = self.db.Model.find_one({'name': self.MODEL_NAME})
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
        count = self.db.Model.find().count()
        name = 'UnitTestModel1'
        features = open('./conf/features.json', 'r').read()
        handler = open('./conf/extract.json', 'r').read()
        post_data = {'importhandler': handler,
                     'features': features}
        resp = self.app.post('/cloudml/model/%s' % name, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue('model' in resp.data)
        new_count = self.db.Model.find().count()
        self.assertEquals(count + 1, new_count)

    def test_post_trained_model(self):
        count = self.db.Model.find().count()
        name = 'UnitTestModel2'
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./model.dat', 'r')
        post_data = {'importhandler': handler,
                     'trainer': trainer}
        resp = self.app.post('/cloudml/model/%s' % name, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue('model' in resp.data)
        new_count = self.db.Model.find().count()
        self.assertEquals(count + 1, new_count)

        model = self.db.Model.find_one({'name': name})
        self.assertEquals(model.name, name)
        self.assertTrue(model.fs.trainer)

    def test_delete(self):
        url = '/cloudml/model/' + self.MODEL_NAME
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
        self.assertEquals(err_data['message'], message)
