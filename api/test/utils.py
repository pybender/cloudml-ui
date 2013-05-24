import unittest
import httplib
import json
import os
from datetime import datetime
from bson.objectid import ObjectId

from api import app


class BaseTestCase(unittest.TestCase):
    FIXTURES = []
    _LOADED_COLLECTIONS = []
    RESOURCE = None

    @classmethod
    def setUpClass(cls):
        app.config['DATABASE_NAME'] = 'cloudml-testdb'
        app.init_db()
        cls.app = app.test_client()

    def setUp(self):
        self.fixtures_load()

    def tearDown(self):
        self.fixtures_cleanup()

    @property
    def db(self):
        return app.db

    @classmethod
    def fixtures_load(cls):
        for fixture in cls.FIXTURES:
            data = _load_fixture_data(fixture)
            for collection_name, documents in data.iteritems():
                cls._LOADED_COLLECTIONS.append(collection_name)
                collection = _get_collection(collection_name)
                for doc in documents:
                    doc['created_on'] = datetime.now()
                    doc['updated_on'] = datetime.now()
                    if '_id' in doc:
                        doc['_id'] = ObjectId(doc['_id'])
                collection.insert(documents)

    @classmethod
    def fixtures_cleanup(cls):
        for collection_name in cls._LOADED_COLLECTIONS:
            collection = _get_collection(collection_name)
            collection.remove()

    def _get_url(self, **kwargs):
        id = kwargs.pop('id', '')
        action = kwargs.pop('action', '')
        search = '&'.join(['%s=%s' % (key, val)
                           for key, val in kwargs.iteritems()])
        params = {'url': self.BASE_URL,
                  'id': "%s/" % id if id else '',
                  'action': "action/%s/" % action if action else '',
                  'search': search}
        return "%(url)s%(id)s%(action)s?%(search)s" % params

    def _check_list(self, show='created_on,type'):
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        url = self.BASE_URL
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s' % (resp.status, url))
        data = json.loads(resp.data)
        self.assertTrue(key in data, data)
        obj_resp = data[key]
        count = self.Model.find().count()
        #self.assertTrue(count, 'Invalid fixtures')
        self.assertEquals(count, len(obj_resp))
        default_fields = self.RESOURCE.DEFAULT_FIELDS or [u'_id', u'name']
        self.assertEquals(obj_resp[0].keys(), default_fields)

        url = self._get_url(show=show)
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s' % (resp.status, url))
        data = json.loads(resp.data)
        obj_resp = data[key][0]
        fields = show.split(',')
        self.assertEquals(len(fields) + 1, len(obj_resp.keys()))
        for field in fields:
            self.assertTrue(field in obj_resp.keys())

    def _check_details(self, show='created_on,type'):
        key = self.RESOURCE.OBJECT_NAME
        url = self._get_url(id=self.obj._id)
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s: %s' %
                          (resp.status, url, resp.data))
        data = json.loads(resp.data)
        self.assertTrue(key in data, data)
        obj_resp = data[key]
        self.assertEquals(str(self.obj._id), obj_resp['_id'])
        self.assertEquals(self.obj.name, obj_resp['name'])

        url = self._get_url(id=self.obj._id, show=show)
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s' % (resp.status, url))
        data = json.loads(resp.data)
        obj_resp = data[key]
        fields = show.split(',')
        self.assertEquals(len(fields) + 1, len(obj_resp.keys()))
        for field in fields:
            self.assertTrue(field in obj_resp.keys())
            self.assertEquals(str(getattr(self.obj, field)),
                              obj_resp[field])

    def _check_post(self, post_data={}, load_model=False):
        count = self.Model.find().count()
        resp = self.app.post(self.BASE_URL, data=post_data)
        self.assertEquals(resp.status_code, httplib.CREATED)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        new_count = self.Model.find().count()
        self.assertEquals(count + 1, new_count)
        if load_model:
            data = json.loads(resp.data)
            _id = data[self.RESOURCE.OBJECT_NAME]['_id']
            obj = self.Model.find_one({'_id': ObjectId(_id)})
            return resp, obj
        return resp


def _get_collection(name):
    callable_model = getattr(app.db, name)
    return callable_model.collection


def _load_fixture_data(filename):
    filename = os.path.join('./api/fixtures/', filename)
    content = open(filename, 'rb').read()
    return json.loads(content)


def dumpdata(document_list, fixture_name):
    from api.serialization import encode_model
    content = json.dumps(document_list, default=encode_model)
    file_path = os.path.join('./api/fixtures/', fixture_name)
    with open(file_path, 'w') as ffile:
        ffile.write(content)
