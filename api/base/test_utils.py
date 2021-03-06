"""
Utility classes and methods for unittesting.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import urllib
import logging
import httplib
import unittest
import json
from flask.ext.testing import TestCase
from sqlalchemy import create_engine
from cloudml.tests.test_utils import StreamPill
import boto3

from api import app
from api.accounts.models import AuthToken
from api.logs.dynamodb.models import LogMessage

AUTH_TOKEN = 'token'
HTTP_HEADERS = [('X-Auth-Token', AUTH_TOKEN)]

# Count of the features in conf/features.json file
FEATURE_COUNT = 35
TARGET_VARIABLE = 'hire_outcome'
FLOAT_ACCURACY = 15


class BaseDbTestCase(TestCase):
    """
    Base class for TestCases that uses database.
    """
    datasets = []

    @property
    def db(self):
        return self.app.sql_db

    @classmethod
    def setUpClass(cls):
        app.config.from_object('api.test_config')
        app.config['MODIFY_DEPLOYED_MODEL'] = False
        app.config['MODIFY_DEPLOYED_IH'] = False
        app.config['CLOUDML_PREDICT_BUCKET_NAME'] = 'test-predict-bucket'

        # if Model is not defined, try get it from resource.
        if hasattr(cls, 'RESOURCE') and not hasattr(cls, 'Model'):
            cls.Model = cls.RESOURCE.Model

        cls.engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        # TODO: do we need this or need to create test db manually?
        try:
            conn = cls.engine.connect()
            conn.close()
        except Exception:  # TODO: catch OperationalError
            logging.info(
                "Can't connect to the test database. Try to create a new one.")
            cls.exec_db_level_sql(
                "create database %s" % app.config['DB_NAME'])

        app.sql_db.session.expunge_all()
        app.sql_db.drop_all()
        app.sql_db.metadata.create_all(cls.engine)
        app.sql_db.create_all()

    @classmethod
    def tearDownClass(cls):
        app.sql_db.session.expunge_all()
        app.sql_db.session.remove()
        app.sql_db.drop_all()
        # cls.dynamodb_mock.stop()
        # cls.s3_mock.stop()

    def setUp(self):
        # Clean all tables
        import os
        self.pill = StreamPill(debug=False)
        self.session = boto3.session.Session()
        boto3.DEFAULT_SESSION = self.session
        self.pill.attach(self.session, os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'pill')))
        self.pill.playback()

        for table in reversed(self.db.metadata.sorted_tables):
            self.db.session.execute(table.delete())
        self.db.session.commit()
        self.db.session.expunge_all()

        # Loading fixtures
        from api.accounts.fixtures import UserData
        if UserData not in self.datasets:
            self.datasets = list(self.datasets)
            self.datasets.append(UserData)

        try:
            self.load_fixtures(*self.datasets)
        except Exception, exc:
            logging.warning(
                'Problem with loading fixture %s: %s', self.datasets, exc)

        from api import celery
        celery.conf['CELERY_ALWAYS_EAGER'] = True
        celery.conf['CELERY_EAGER_PROPAGATES_EXCEPTIONS'] = False

    def tearDown(self):
        self.db.session.remove()
        self.db.session.expunge_all()

    # Utility methods
    @classmethod
    def exec_db_level_sql(cls, sql):
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
    """
    Mixin contains common methods for testing the resource class.
    """
    BASE_URL = ''

    def check_list(self, show='', data={},
                   query_params={}, count=None, with_paging=False):
        key = "%ss" % self.RESOURCE.OBJECT_NAME
        resp_data = self._check(show=show, **data)
        self.assertTrue(key in resp_data, resp_data)
        obj_resp = resp_data[key]

        if count is None:
            count = self.Model.query.filter_by(**query_params).count()

        if self.RESOURCE.NEED_PAGING:
            # Checking the paging
            per_page = 20
            paged_count = count if count < per_page else per_page
            self.assertEquals(resp_data['page'], 1)
            self.assertEquals(resp_data['per_page'], 20)
            self.assertEquals(resp_data['total'], count)
            self.assertEquals(paged_count, len(obj_resp), obj_resp)
        else:
            self.assertEquals(count, len(obj_resp), obj_resp)

        if len(obj_resp):
            obj = obj_resp[-1]  # TODO: invest. that 1st el contains all fields
            fields = self._get_fields(show)
            self.assertEquals(
                len(fields), len(obj.keys()),
                "Should display %s fields. Actual fields are: %s" %
                (fields, obj.keys()))
            for field in fields:
                self.assertTrue(field in obj.keys())

        return resp_data

    def check_details(self, obj=None, show='', data={},
                      fixture_cls=None):
        if obj:
            self.obj = obj
        key = self.RESOURCE.OBJECT_NAME
        resp_data = self._check(show=show, id=self.obj.id, **data)
        self.assertTrue(key in resp_data, resp_data)

        obj = resp_data[key]
        fields = self._get_fields(show)
        self.assertEquals(len(fields), len(obj.keys()))
        for field in fields:
            self.assertTrue(field in obj.keys())

        if fixture_cls:
            self._check_object_with_fixture_class(obj, fixture_cls)

        return resp_data

    def check_edit(self, data={}, **kwargs):
        count = self.Model.query.count()
        obj_id = kwargs.get('id', None)
        method = 'put' if obj_id else 'post'
        resp_data = self._check(method=method, data=data, **kwargs)

        self.assertEquals(count if obj_id else count + 1,
                          self.Model.query.count())

        obj_id = resp_data[self.RESOURCE.OBJECT_NAME]['id']
        self.assertTrue(obj_id, "Invalid response: {0}".format(resp_data))
        obj = self.Model.query.get(obj_id)
        return resp_data, obj

    def check_edit_error(self, post_data, errors, **data):
        from api.base.resources import ERR_INVALID_DATA
        count = self.Model.query.count()
        url = self._get_url(**data)
        obj_id = data.get('id', None)
        method = 'put' if obj_id else 'post'
        resp = getattr(self.client, method)(
            url, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        resp_data = json.loads(resp.data)
        err_data = resp_data['response']['error']
        self.assertEquals(err_data['code'], ERR_INVALID_DATA)
        self._check_errors(err_data, errors)
        self.assertEquals(count, self.Model.query.count())

    def check_delete(self, obj=None, check_model_deleted=True):
        if obj is None:
            obj = self.obj

        self.assertTrue(obj)
        url = self._get_url(id=obj.id)
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 204)

        if check_model_deleted:
            self.assertFalse(self.Model.query.filter_by(id=obj.id).count())

    def check_readonly(self):
        url = self._get_url(id=self.obj.id)

        # Deleting
        resp = self.client.delete(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

        # Edditing
        post_data = {'name': 'test'}
        resp = getattr(self.client, 'put')(
            url, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

        # Adding
        url = self._get_url()
        resp = getattr(self.client, 'post')(
            url, data=post_data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

    def assertDeepAlmostEqual(self, expected, actual):
        """
        Assert that two complex structures have almost equal contents.

        Compares lists, dicts and tuples recursively. Checks numeric values
        using test_case's assertAlmostEqual and
        checks all other values with assertEqual.
        Accepts additional positional and keyword arguments and pass those
        intact to assertAlmostEqual() (that's how you specify comparison
        precision).
        """
        if isinstance(expected, (float, long, complex)):
            self.assertAlmostEqual(expected, actual, places=FLOAT_ACCURACY)
        elif isinstance(expected, (list, tuple, set)):
            self.assertEqual(len(expected), len(actual))
            for index in xrange(len(expected)):
                v1, v2 = expected[index], actual[index]
                self.assertDeepAlmostEqual(v1, v2)
        elif isinstance(expected, dict):
            self.assertEqual(set(expected), set(actual))
            for key in expected:
                self.assertDeepAlmostEqual(expected[key], actual[key])
        else:
            self.assertEqual(expected, actual)

    def assertNumAlmostEqual(self, n1, n2, places=FLOAT_ACCURACY):
        self.assertAlmostEqual(n1, n2, places=places)

    def assertDictEqual(self, d1, d2, msg=None):  # assertEqual uses for dicts
        for k, v1 in d1.iteritems():
            self.assertIn(k, d2, msg)
            v2 = d2[k]
            if(isinstance(v1, collections.Iterable) and
               not isinstance(v1, basestring)):
                self.assertItemsEqual(v1, v2, msg)
            else:
                self.assertEqual(v1, v2, msg)
        return True

    def _get_resp_object(self, resp_data, is_list=True, num=-1):
        if is_list:
            key = "%ss" % self.RESOURCE.OBJECT_NAME
            obj_resp = resp_data[key]
            return obj_resp[num]
        else:
            return resp_data[self.RESOURCE.OBJECT_NAME]

    def _check_object_with_fixture_class(self, obj, fixture_cls):
        print obj, obj.keys()
        for key, val in obj.iteritems():
            if key == 'id':
                self.assertTrue(obj['id'])
                continue
            self.assertEquals(getattr(fixture_cls, key), obj[key])

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
            "Resp of %s %s: %s" % (url, resp.status_code, resp.data))
        if load_json:
            return json.loads(resp.data)
        return resp.data

    def _get_fields(self, show):
        if show:
            fields = show.split(',')
            if 'id' not in fields:
                fields.append('id')
            return set(fields)
        else:
            return self.RESOURCE.DEFAULT_FIELDS or [u'id', u'name']

    def _check_not_allowed_method(self, method='delete', url=None, data={}):
        if url is None:
            url = self.BASE_URL

        mthd = getattr(self.client, method)
        resp = mthd(url, headers=HTTP_HEADERS, data=data)
        self.assertEquals(resp.status_code, 400)
        msg = json.loads(resp.data)['response']['error']['message']
        self.assertEquals(msg, "%s is not allowed" % method)


class DefaultsCheckMixin(object):
    def _check_is_default(self, Cls):
        obj = Cls.query.filter_by(is_default=False)[0]
        obj.is_default = True
        obj.save()

        obj = Cls.query.get(obj.id)
        self.assertTrue(obj.is_default)
        defaults = Cls.query.filter_by(is_default=True)
        self.assertEquals(defaults.count(), 1, list(defaults))
