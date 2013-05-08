from flask import Flask
from werkzeug.routing import BaseConverter
from mongokit import Connection
from flask.ext import restful
from celery import Celery

from celery.signals import after_setup_task_logger
import logging

# class BroadcastLogHandler(logging.Handler):
#     def __init__(self):
#         self.broadcaster = None#Producer()
#         self.level = 0
#         self.filters = []
#         self.lock = 0
#         self.machine = os.uname()[1]

#     def emit(self, record):
#         # Send the log message to the broadcast queue
#         message = {"source":"logger","machine":self.machine, "message":record.msg % record.args, "level":record.levelname, "pathname":record.pathname, "lineno":record.lineno, "exception":record.exc_info}
#         self.broadcaster.message(message)

def foo_tasks_setup_logging(**kw):
    logger = logging.getLogger('celery')
    if not logger.handlers:
        handler = logging.FileHandler('tasks.log')
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = True

after_setup_task_logger.connect(foo_tasks_setup_logging)


app = Flask(__name__)
app.config.from_object('api.config')

connection = Connection()
db_name = app.config['DATABASE_NAME']
if app.config.get('TESTING'):
    db_name += '-test'

app.db = getattr(connection, db_name)

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
