import unittest
import httplib
import json
import os
import re
from datetime import datetime
from bson.objectid import ObjectId
from celery.task.base import Task

from api import app


MODEL_ID = '519318e6106a6c0df349bc0b'

# Count of the features in conf/features.json file
FEATURE_COUNT = 37
TARGET_VARIABLE = 'hire_outcome'

AUTH_TOKEN = '123'
HTTP_HEADERS = [('X-Auth-Token', AUTH_TOKEN)]


class BaseTestCase(unittest.TestCase):
    FIXTURES = []
    _LOADED_COLLECTIONS = []
    RESOURCE = None

    @classmethod
    def setUpClass(cls):
        app.config['DATABASE_NAME'] = 'cloudml-testdb'
        app.config['DATA_FOLDER'] = 'test_data'
        app.conn.drop_database(app.config['DATABASE_NAME'])
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
        from mongokit.document import DocumentProperties, R

        if 'users.json' not in cls.FIXTURES:
            cls.FIXTURES = ('users.json',) + tuple(cls.FIXTURES)

        for fixture in cls.FIXTURES:
            data = _load_fixture_data(fixture)
            for collection_name, documents in data.iteritems():
                cls._LOADED_COLLECTIONS.append(collection_name)
                Model = getattr(app.db, collection_name)
                for doc in documents:
                    related_objects = []
                    obj = Model()
                    for key, val in doc.iteritems():
                        if val is None:
                            continue

                        if key == '_id':
                            obj['_id'] = ObjectId(val)
                        else:
                            field_type = Model.structure[key]
                            if field_type == datetime:
                                obj[key] = datetime.now()
                            elif field_type == long:
                                obj[key] = long(doc[key])
                            elif isinstance(field_type, DocumentProperties) \
                                    or isinstance(field_type, R):
                                related_objects.append({
                                    'id': doc['_id'],
                                    'collection': collection_name,
                                    'related_collection': val['$ref'],
                                    'related_id': val['$id'],
                                    'fieldname': key})
                                doc[key] = None
                            else:
                                obj[key] = doc[key]
                    obj.save()

                    # Save db refs
                    for rel in related_objects:
                        RelModel = getattr(app.db, rel['related_collection'])
                        related_obj = RelModel.find_one({
                            '_id': ObjectId(rel['related_id'])})
                        setattr(obj, rel['fieldname'], related_obj)
                        obj.save()

    @classmethod
    def fixtures_cleanup(cls):
        for collection_name in cls._LOADED_COLLECTIONS:
            collection = _get_collection(collection_name)
            collection.remove()

    @classmethod
    def post_trained_model(cls, model_name):
        handler = open('./conf/extract.json', 'r').read()
        trainer = open('./api/fixtures/model.dat', 'r').read()
        post_data = {'test_import_handler_file': handler,
                     'train_import_handler_file': handler,
                     'trainer': trainer,
                     'name': model_name}
        resp = cls.app.post('/cloudml/models/', data=post_data,
                            headers=HTTP_HEADERS)
        assert resp.status_code == httplib.CREATED

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

    def _check_list(self, show='created_on,type', query_params={}):
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        url = self.BASE_URL
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s' % (resp.status, url))
        data = json.loads(resp.data)
        self.assertTrue(key in data, data)
        obj_resp = data[key]
        count = self.Model.find(query_params).count()
        #self.assertTrue(count, 'Invalid fixtures')
        self.assertEquals(count, len(obj_resp), obj_resp)
        default_fields = self.RESOURCE.DEFAULT_FIELDS or [u'_id', u'name']
        self.assertEquals(obj_resp[0].keys(), list(default_fields))

        url = self._get_url(show=show)
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s' % (resp.status, url))
        data = json.loads(resp.data)
        obj_resp = data[key][0]
        fields = self.__get_fields(show)
        valid_count = len(fields) if '_id' in fields \
            else len(fields) + 1
        self.assertEquals(valid_count, len(obj_resp.keys()))

        for field in fields:
            self.assertTrue(field in obj_resp.keys())

    def _check_details(self, show='created_on,type'):
        key = self.RESOURCE.OBJECT_NAME
        url = self._get_url(id=self.obj._id)
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s: %s' %
                          (resp.status, url, resp.data))
        data = json.loads(resp.data)
        self.assertTrue(key in data, data)
        obj_resp = data[key]
        self.assertEquals(str(self.obj._id), obj_resp['_id'])
        self.assertEquals(self.obj.name, obj_resp['name'])

        url = self._get_url(id=self.obj._id, show=show)
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK,
                          'Got %s when trying get %s' % (resp.status, url))
        data = json.loads(resp.data)
        obj_resp = data[key]
        _id = data[self.RESOURCE.OBJECT_NAME]['_id']
        doc = self.Model.find_one({'_id': ObjectId(_id)})

        fields = self.__get_fields(show)
        valid_count = len(fields) if '_id' in fields \
            else len(fields) + 1
        self.assertEquals(valid_count, len(obj_resp.keys()))

        for field in fields:
            self.assertTrue(field in obj_resp.keys(),
                            'Field %s is not in resp: %s' %
                            (field, obj_resp.keys()))
            self.assertEquals(str(doc.get(field)),
                              str(obj_resp.get(field)))

    def __get_fields(self, show):
        if show:
            return show.split(',')
        else:
            return self.RESOURCE.DEFAULT_FIELDS or [u'_id', u'name']

    def _check_post(self, post_data={}, error='', load_model=False, action=None):
        count = self.Model.find().count()
        url = self._get_url(action=action) if action else self.BASE_URL
        resp = self.app.post(url, data=post_data, headers=HTTP_HEADERS)
        if error:
            from api.utils import ERR_INVALID_DATA
            # Checking validation error
            self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
            data = json.loads(resp.data)
            err_data = data['response']['error']
            self.assertEquals(err_data['code'], ERR_INVALID_DATA)
            self.assertTrue(error in err_data['message'],
                            "Response message is: %s" % err_data['message'])
        else:
            print resp.data
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

    def _check_put(self, post_data={}, error='', load_model=False, action=None):
        if action:
            url = self._get_url(id=self.obj._id, action=action)
        else:
            url = self._get_url(id=self.obj._id)

        resp = self.app.put(url, data=post_data, headers=HTTP_HEADERS)
        if error:
            from api.utils import ERR_INVALID_DATA
            # Checking validation error
            self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
            data = json.loads(resp.data)
            err_data = data['response']['error']
            self.assertEquals(err_data['code'], ERR_INVALID_DATA)
            self.assertTrue(error in err_data['message'],
                            "Response message is: %s" % err_data['message'])
        else:
            self.assertEquals(resp.status_code, httplib.OK)
            self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)

            if load_model:
                data = json.loads(resp.data)
                _id = data[self.RESOURCE.OBJECT_NAME]['_id']
                obj = self.Model.find_one({'_id': ObjectId(_id)})
                return resp, obj

        return resp

    def _check_filter(self, filter_params, query_params=None):
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        if query_params is None:
            query_params = filter_params

        url = self._get_url(**filter_params)
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        count = self.db.Model.find(query_params).count()
        self.assertEquals(count, len(data[key]))

    def _check_delete(self):
        self.assertTrue(self.obj)
        url = self._get_url(id=self.obj._id)
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)

        resp = self.app.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 204)

        obj = self.Model.find_one({'_id': self.obj._id})
        self.assertFalse(obj)

    def check_related_docs_existance(self, Model, exist=True,
                                     msg=''):
        """
        Checks whether documents exist.
        """
        obj_list = Model.find(self.RELATED_PARAMS)
        self.assertEqual(bool(obj_list.count()), exist, msg)
        return obj_list


class CeleryTestCaseBase(BaseTestCase):

    def setUp(self):
        super(CeleryTestCaseBase, self).setUp()
        self.applied_tasks = []

        self.task_apply_async_orig = Task.apply_async

        @classmethod
        def new_apply_async(task_class, args=None, kwargs=None, **options):
            self.handle_apply_async(task_class, args, kwargs, **options)

        # monkey patch the regular apply_sync with our method
        Task.apply_async = new_apply_async

    def tearDown(self):
        super(CeleryTestCaseBase, self).tearDown()

        # Reset the monkey patch to the original method
        Task.apply_async = self.task_apply_async_orig

    def handle_apply_async(self, task_class, args=None, kwargs=None, **options):
        self.applied_tasks.append((task_class, tuple(args), kwargs))

    def assert_task_sent(self, task_class, *args, **kwargs):
        was_sent = any(task_class == task[0] and args == task[1] and kwargs == task[2]
                       for task in self.applied_tasks)
        self.assertTrue(was_sent, 'Task not called w/class %s and args %s' % (task_class, args))

    def assert_task_not_sent(self, task_class):
        was_sent = any(task_class == task[0] for task in self.applied_tasks)
        self.assertFalse(was_sent, 'Task was not expected to be called, but was.  Applied tasks: %s' % self.applied_tasks)


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
