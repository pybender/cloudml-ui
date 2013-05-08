from flask import Flask
from werkzeug.routing import BaseConverter
from mongokit import Connection
from flask.ext import restful
from celery import Celery


app = Flask(__name__)
app.config.from_object('api.config')

connection = Connection()
db_name = app.config['DATABASE_NAME']
if app.config.get('TESTING'):
    db_name += '-test'

app.db = getattr(connection, db_name)


from mongotools.pubsub import Channel

app.chan = Channel(app.db, 'log')
app.chan.ensure_channel()

app.chan.sub('test_log')


celery = Celery('cloudml')
celery.add_defaults(lambda: app.config)
api = restful.Api(app)


class RegExConverter(BaseConverter):
    """
    Converter that allows routing to specific functions according to given
    regular expression.

    """
    def __init__(self, url_map, *items):
        super(RegExConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegExConverter


import views
