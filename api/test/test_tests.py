import httplib
import json

from utils import BaseTestCase


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
        tests = self.db.Test.find({'model_name': self.MODEL_NAME})
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
        test = self.db.Test.find_one({'model_name': self.MODEL_NAME,
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
        test = self.db.Test.find_one(params)
        self.assertEquals(test, None, test)

        params = {'model_name': self.MODEL_NAME,
                  'test_name': self.TEST_NAME}
        examples = self.db.TestExample.find(params).count()
        self.assertFalse(examples, "%s test examples was not \
deleted" % examples)
        other_examples = self.db.TestExample.find().count()
        self.assertTrue(other_examples, "All examples was deleted!")

    def _get_url(self, model, test=None, search=None):
        if test:
            return '/cloudml/model/%s/test/%s?%s' % (model, test, search)
        else:
            return '/cloudml/model/%s/tests?%s' % (model, search)
