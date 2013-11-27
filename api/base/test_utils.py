import urllib
import httplib
import json
from flask.ext.testing import TestCase
from sqlalchemy import create_engine

from api import app

AUTH_TOKEN = '123'
HTTP_HEADERS = [('X-Auth-Token', AUTH_TOKEN)]


class BaseDbTestCase(TestCase):
    """
    Base class for TestCases that uses database.
    """
    TESTING = True

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
            self.exec_db_level_sql("create database %s" % app.config['DB_NAME'])

        self.db.metadata.create_all(self.engine)
        self.db.create_all()

        # Loading fixtures
        from api.accounts.fixtures import UserData
        self.load_fixtures(UserData)

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
            count = self.Model.query.find(query_params).count()

        self.assertEquals(count, len(obj_resp), obj_resp)
        # TODO: check that show works
        return resp_data

    def _get_url(self, **kwargs):
        id = kwargs.pop('id', '')
        action = kwargs.pop('action', '')
        params = {'url': self.BASE_URL,
                  'id': "%s/" % id if id else '',
                  'action': "action/%s/" % action if action else '',
                  'search': urllib.urlencode(kwargs)}
        return "%(url)s%(id)s%(action)s?%(search)s" % params

    def _check(self, **kwargs):
        load_json = kwargs.pop('load_json', True)
        url = self._get_url(**kwargs)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(
            resp.status_code, httplib.OK,
            "Resp %s: %s" % (resp.status_code, resp.data))
        if load_json:
            return json.loads(resp.data)
        return resp.data
