import logging
from logging import config as logging_config
import re
from flask import Flask
from werkzeug.routing import BaseConverter
from mongokit import Connection
from mongotools.pubsub import Channel
from pymongo.cursor import _QUERY_OPTIONS
from flask.ext import restful
from celery import Celery
from kombu import Queue
from flask.ext.sqlalchemy import SQLAlchemy


class RegExConverter(BaseConverter):
    """
    Converter that allows routing to specific functions according
    to given regular expression.
    """
    def __init__(self, url_map, *items):
        super(RegExConverter, self).__init__(url_map)
        self.regex = items[0]


class LogChannel(Channel):    # pragma: no cover
    def cursor(self, query_params={}, await=False):
        if not self._callbacks:
            return iter([])
        spec = {'ts': {'$gt': self._position}}
        spec.update(query_params)
        regex = '|'.join(cb.pattern for cb in self._callbacks)
        spec['k'] = re.compile(regex)
        if await:
            options = dict(
                tailable=True,
                await_data=True)
        else:
            options = {}
        q = self.db[self.name].find(spec, **options)
        q = q.hint([('$natural', 1)])
        if await:
            q = q.add_option(_QUERY_OPTIONS['oplog_replay'])
        return q


class App(Flask):
    PUBSUB_CHANNELS = {'runtest_log': ('test', ),
                       'trainmodel_log': ('model', ),
                       'importdata_log': ('handler', )}

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        self.config.from_object('api.config')
        #self.config.from_envvar('CLOUDML_CONFIG', silent=True)
        self.conn = Connection(host=self.config.get('DATABASE_HOST', 'localhost'))
        self.url_map.converters['regex'] = RegExConverter

    @property
    def db(self):
        if not hasattr(self, '_db'):
            self.init_db()
        return self._db

    def init_db(self):
        db_name = self.config['DATABASE_NAME']
        self._db = getattr(self.conn, db_name)
        #from pymongo.son_manipulator import AutoReference, NamespaceInjector
        #self._db.add_son_manipulator(NamespaceInjector()) # inject _ns
        #self._db.add_son_manipulator(AutoReference(self._db))

        self.chan = LogChannel(self._db, 'log')
        self.chan.ensure_channel()
        for name in self.PUBSUB_CHANNELS.keys():
            self.chan.sub(name)

    @property
    def sql_db(self):
        if not hasattr(self, '_sql_db'):
            self.init_sql_db()
        return self._sql_db

    def init_sql_db(self):
        self._sql_db = SQLAlchemy(self)

def create_app():
    return App(__name__)

app = create_app()

celery = Celery('cloudml')

for instance in app.db.instances.find():
    app.config['CELERY_QUEUES'].append(Queue(instance['name'],
                                             routing_key='%s.#' % instance['name']))
celery.add_defaults(lambda: app.config)


class Api(restful.Api):
    def add_resource(self, resource, *urls, **kwargs):
        """Adds a resource to the api.

        :param resource: the class name of your resource
        :type resource: Resource
        :param urls: one or more url routes to match for the resource, standard
                     flask routing rules apply.  Any url variables will be
                     passed to the resource method as args.
        :type urls: str

        :param endpoint: endpoint name (defaults to Resource.__name__.lower()
                         can be used to reference this route in Url fields
                         see: Fields
        :type endpoint: str


        Examples:
            api.add_resource(HelloWorld, '/', '/hello')
        """
        add_standard_urls = kwargs.get('add_standard_urls', True)
        endpoint = kwargs.get('endpoint') or resource.__name__.lower()

        if endpoint in self.app.view_functions.keys():
            previous_view_class = self.app.view_functions[endpoint].func_dict['view_class']
            if previous_view_class != resource:
                raise ValueError('This endpoint (%s) is already set to the class %s.' % (endpoint, previous_view_class.__name__))

        resource.mediatypes = self.mediatypes_method()  # Hacky
        resource_func = self.output(resource.as_view(endpoint))

        for decorator in self.decorators:
            resource_func = decorator(resource_func)

        for part in urls:
            base_url = self.prefix + part
            self.app.add_url_rule(base_url, view_func=resource_func)
            if add_standard_urls:
                url = base_url + '<regex("[\w\.]*"):id>/'
                self.app.add_url_rule(url, view_func=resource_func)
                url = base_url + 'action/<regex("[\w\.]*"):action>/'
                self.app.add_url_rule(self.prefix + url, view_func=resource_func)
                url = base_url + '<regex("[\w\.]*"):id>/' + 'action/<regex("[\w\.]*"):action>/'
                self.app.add_url_rule(self.prefix + url, view_func=resource_func)

api = Api(app)

logging_config.dictConfig(app.config['LOGGING'])

import views
import models
