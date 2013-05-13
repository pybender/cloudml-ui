import logging
from flask import Flask
from werkzeug.routing import BaseConverter
from mongokit import Connection
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


class App(Flask):
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

        from mongotools.pubsub import Channel
        self.chan = Channel(self._db, 'log')
        self.chan.ensure_channel()
        self.chan.sub('runtest_log')
        self.chan.sub('trainmodel_log')


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
