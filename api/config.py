SECRET_KEY = 'CHANGE_ME'
#SQLALCHEMY_DATABASE_URI = 'sqlite:///cloudml.db'
DATABASE_NAME = 'main_cloudml'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
DATA_FOLDER = './data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = True

# Celery specific settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
#BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
#BROKER_URL = 'mongodb://localhost:27017/cloudmlqueue'
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = ''
CELERY_IMPORTS = ('api.models', 'api', 'api.tasks')

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = [
    Queue('default', routing_key='task.#')
]
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'



AMAZON_ACCESS_TOKEN = 'AKIAJYNNIPFWF2ABW42Q'
AMAZON_TOKEN_SECRET = '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'
AMAZON_BUCKET_NAME = 'odesk-match-cloudml'

try:
    from api.local_config import *
except ImportError:
    pass
