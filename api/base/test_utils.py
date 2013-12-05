import urllib
import os
import logging
import httplib
import unittest
import json
from datetime import datetime
from flask.ext.testing import TestCase
from sqlalchemy import create_engine

from api import app

SOMEBODY_AUTH_TOKEN = '123'
SOMEBODY_HTTP_HEADERS = [('X-Auth-Token', SOMEBODY_AUTH_TOKEN)]

AUTH_TOKEN = 'token'
HTTP_HEADERS = [('X-Auth-Token', AUTH_TOKEN)]


class BaseDbTestCase(TestCase):
    """
    Base class for TestCases that uses database.
    """
    TESTING = True
    datasets = []

    @property
    def db(self):
        return self.app.sql_db

    def setUp(self):
        self.engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        # TODO: do we need this or need to create test db manually?
        try:
            conn = self.engine.connect()
            conn.close()
        except Exception:  # TODO: catch OperationalError
            self.exec_db_level_sql(
                "create database %s" % app.config['DB_NAME'])

        self.db.metadata.create_all(self.engine)
        self.db.create_all()

        # Loading fixtures
        from api.accounts.fixtures import UserData
        try:
            self.load_fixtures(UserData)
        except Exception, exc:
            logging.error('Exception while load user data: %s', exc)
        for ds in set(self.datasets):
            self.load_fixtures(ds)

        # Fixing celery config
        from api import celery
        celery.conf['CELERY_ALWAYS_EAGER'] = True
        celery.conf['CELERY_EAGER_PROPAGATES_EXCEPTIONS'] = False

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()

    # Utility methods
    def exec_db_level_sql(self, sql):
        pengine = create_engine(app.config['DB_FORMAT_URI'] % "postgres")
        create_db_conn = pengine.connect()
        create_db_conn.execute("commit")
        create_db_conn.execute(sql)
        create_db_conn.close()

    def create_app(self):
        self.app = app
        return app

    def load_fixtures(self, *args):
        # TODO: Check https://github.com/mitsuhiko/flask-sqlalchemy/pull/89
        # and update version of Flask-Sqlalchemy
        from api import models
        from fixture import SQLAlchemyFixture
        from fixture.style import NamedDataStyle

        db = SQLAlchemyFixture(
            env=models, style=NamedDataStyle(), engine=self.engine)
        data = db.data(*args)
        data.setup()
        db.dispose()


class TestChecksMixin(object):
    BASE_URL = ''

    def check_list(self, show='', data={}, query_params={}, count=None):
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        resp_data = self._check(show=show, **data)
        self.assertTrue(key in resp_data, resp_data)
        obj_resp = resp_data[key]

        if count is None:
            count = self.Model.query.filter_by(**query_params).count()

        self.assertEquals(count, len(obj_resp), obj_resp)
        # TODO: check that show works
        return resp_data

    def check_details(self, obj=None, show='', data={}):
        if obj:
            self.obj = obj
        key = self.RESOURCE.OBJECT_NAME
        resp_data = self._check(show=show, id=self.obj.id, **data)
        self.assertTrue(key in resp_data, resp_data)
        return resp_data

    def check_edit(self, data={}, **kwargs):
        count = self.Model.query.count()
        obj_id = kwargs.get('id', None)
        method = 'put' if obj_id else 'post'
        resp_data = self._check(method=method, data=data, **kwargs)

        self.assertEquals(count if obj_id else count + 1,
                          self.Model.query.count())

        obj_id = resp_data[self.RESOURCE.OBJECT_NAME]['id']
        obj = self.Model.query.get(obj_id)
        return resp_data, obj

    def check_edit_error(self, post_data, errors, **data):
        from api.utils import ERR_INVALID_DATA
        count = self.Model.query.count()
        url = self._get_url(**data)
        resp = self.client.post(url, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        resp_data = json.loads(resp.data)
        err_data = resp_data['response']['error']
        self.assertEquals(err_data['code'], ERR_INVALID_DATA)
        self._check_errors(err_data, errors)
        self.assertEquals(count, self.Model.query.count())

    def check_delete(self, obj=None):
        if obj is None:
            obj = self.obj

        self.assertTrue(obj)
        url = self._get_url(id=obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 204)

        self.assertFalse(self.Model.query.filter_by(id=obj.id).count())

    def _check_errors(self, err_data, errors):
        err_list = err_data['errors']
        errors_dict = dict([(item['name'], item['error'])
                            for item in err_list])
        logging.info("Response is: %s", errors_dict)
        for field, err_msg in errors.iteritems():
            self.assertTrue(
                field in errors_dict,
                "Should be err for field %s: %s" % (field, err_msg))
            self.assertEquals(err_msg, errors_dict[field])
        self.assertEquals(len(errors_dict), len(errors),
                          errors_dict.keys())

    def _get_url(self, **kwargs):
        id = kwargs.pop('id', '')
        action = kwargs.pop('action', '')
        params = {'url': self.BASE_URL,
                  'id': "%s/" % id if id else '',
                  'action': "action/%s/" % action if action else '',
                  'search': urllib.urlencode(kwargs)}
        return "%(url)s%(id)s%(action)s?%(search)s" % params

    def _check(self, **kwargs):
        method = kwargs.pop('method', 'get')
        data = kwargs.pop('data', {})
        load_json = kwargs.pop('load_json', True)
        url = self._get_url(**kwargs)
        mthd = getattr(self.client, method)
        resp = mthd(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(
            resp.status_code, 201 if method == 'post' else httplib.OK,
            "Resp %s: %s" % (resp.status_code, resp.data))
        if load_json:
            return json.loads(resp.data)
        return resp.data


class BaseMongoTestCase(unittest.TestCase):
    FIXTURES = []
    _LOADED_COLLECTIONS = []
    RESOURCE = None

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        for root, dirs, files in os.walk(app.config['DATA_FOLDER']):
            for f in files:
                os.unlink(os.path.join(root, f))

    def setUp(self):
        self.fixtures_load()

    def tearDown(self):
        self.fixtures_cleanup()

    @property
    def mongo_db(self):
        return app.db

    @classmethod
    def fixtures_load(cls):
        from mongokit.document import DocumentProperties, R

        # if 'users.json' not in cls.FIXTURES:
        #     cls.FIXTURES = ('users.json',) + tuple(cls.FIXTURES)

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
                            from bson.objectid import ObjectId
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


def _get_collection(name):
    callable_model = getattr(app.db, name)
    return callable_model.collection


def _load_fixture_data(filename):
    filename = os.path.join('./api/fixtures/', filename)
    content = open(filename, 'rb').read()
    return json.loads(content)
