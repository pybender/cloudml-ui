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
        from api import models
        from mongokit.document import DocumentProperties, R
        related_objects = []
        for fixture in cls.FIXTURES:
            data = _load_fixture_data(fixture)
            for collection_name, documents in data.iteritems():
                cls._LOADED_COLLECTIONS.append(collection_name)
                collection = _get_collection(collection_name)
                Model = getattr(models, collection_name)
                for doc in documents:
                    for key, val in doc.iteritems():
                        if key == '_id':
                            doc['_id'] = ObjectId(val)
                        else:
                            field_type = Model.structure[key]
                            if field_type == datetime:
                                doc[key] = datetime.now()
                            elif isinstance(field_type, DocumentProperties):
                                if val:
                                    RelModel = getattr(app.db, val['$ref'])
                                    doc[key] = RelModel.find_one({'_id': ObjectId(val['$id'])})
                            elif isinstance(field_type, R):
                                if val:
                                    related_objects.append({'id': doc['_id'],
                                                            'collection': collection_name,
                                                            'related_collection': val['$ref'],
                                                            'related_id': val['$id'],
                                                            'fieldname': key})
                                    doc[key] = None
                collection.insert(documents)

        for related_item in related_objects:
            Model = getattr(app.db, related_item['collection'])
            RelModel = getattr(app.db, related_item['related_collection'])
            obj = Model.find_one({'_id': ObjectId(related_item['id'])})
            related_obj = RelModel.find_one({'_id': ObjectId(related_item['related_id'])})

            setattr(obj, related_item['fieldname'], related_obj)
            obj.save()

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
        print obj_resp
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
        self.assertFalse(was_sent, 'Task was not expected to be called, but was.  Applied tasks: %s' %                 self.applied_tasks)


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
