SECRET_KEY = 'CHANGE_ME'
DATABASE_NAME = 'cloudml'
STATIC_ROOT = None

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/cloudml_data'

UPLOAD_FOLDER = 'models'
DATA_FOLDER = './data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = False

# Celery specific settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
#BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
#BROKER_URL = 'mongodb://localhost:27017/cloudmlqueue'
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@localhost:5672//'
CELERY_IMPORTS = ('api.models', 'api', 'api.tasks')
CELERYD_MAX_TASKS_PER_CHILD = 1

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = [
    Queue('default', routing_key='task.#')
]
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

REQUESTING_INSTANCE_COUNTDOWN = 20
REQUESTING_INSTANCE_MAX_RETRIES = 30

EXAMPLES_CHUNK_SIZE = 10

MULTIPART_UPLOAD_CHUNK_SIZE = 8192

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'normal': {
            'format': '[%(asctime)s] %(levelname)s - %(message)s'
        },
    },
    'filters': {},
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'normal'
        },
    },
    'loggers': {
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'boto': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

try:
    from api.local_config import *
except ImportError:
    pass
