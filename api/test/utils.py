import unittest
import json
import os

from api import app


class BaseTestCase(unittest.TestCase):
    FIXTURES = []
    _LOADED_COLLECTIONS = []

    @classmethod
    def setUpClass(cls):
        app.config['DATABASE_NAME'] = 'cloudml-test'
        app.init_db()
        cls.app = app.test_client()

    def setUp(self):
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


def dumpdata(document_list, fixture_name):
    from api.serialization import encode_model
    content = json.dumps(document_list, default=encode_model)
    file_path = os.path.join('./api/fixtures/', fixture_name)
    with open(file_path, 'w') as ffile:
        ffile.write(content)
