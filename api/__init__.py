import logging
import re
from flask import Flask
from werkzeug.routing import BaseConverter
from mongokit import Connection
from mongotools.pubsub import Channel
from pymongo.cursor import _QUERY_OPTIONS
from flask.ext import restful
from celery import Celery


class RegExConverter(BaseConverter):
    """
    Converter that allows routing to specific functions according
    to given regular expression.
    """
    def __init__(self, url_map, *items):
        super(RegExConverter, self).__init__(url_map)
        self.regex = items[0]


class LogChannel(Channel):
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
                       'trainmodel_log': ('model', )}

    def __init__(self, connection, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        self.conn = connection
        self.config.from_object('api.config')
        self.url_map.converters['regex'] = RegExConverter

    @property
    def db(self):
        if not hasattr(self, '_db'):
            self.init_db()
        return self._db

    def init_db(self):
        db_name = self.config['DATABASE_NAME']
        self._db = getattr(self.conn, db_name)

        self.chan = LogChannel(self._db, 'log')
        self.chan.ensure_channel()
        for name in self.PUBSUB_CHANNELS.keys():
            self.chan.sub(name)


connection = Connection()
app = App(connection, __name__)

celery = Celery('cloudml')
celery.add_defaults(lambda: app.config)
api = restful.Api(app)

logging_level = logging.INFO
logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s',
                    level=logging_level)

import views
import models
