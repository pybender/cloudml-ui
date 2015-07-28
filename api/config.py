from kombu import Queue
from datetime import timedelta

SECRET_KEY = 'CHANGE_ME'
STATIC_ROOT = None

SQLALCHEMY_DATABASE_URI = \
    'postgresql://postgres:postgres@localhost/cloudml_data'


UPLOAD_FOLDER = 'models'
DATA_FOLDER = './data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = False
TEST_MODE = False

# Celery specific settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True

# Note: other celery brockers:
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@localhost:5672//'
CELERY_IMPORTS = (
    'api.models', 'api', 'api.import_handlers.tasks',
    'api.instances.tasks', 'api.ml_models.tasks',
    'api.model_tests.tasks', 'api.servers.tasks')
CELERYD_MAX_TASKS_PER_CHILD = 1

CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'api.instances.tasks.synchronyze_cluster_list',
        'schedule': timedelta(seconds=30)
    },
}


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
        # 'sqlalchemy.engine': {
        #     'handlers': ['console'],
        #     'level': 'INFO',
        #     'propagate': True,
        # },
    }
}

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = False
SEND_ERROR_EMAILS = False

# Name and email addresses of recipients
ADMINS = (
    ("Nikolay Melnik", "nmelnik@odesk.com"),
    ("Nader Soliman", "nsoliman@elance-odesk.com"),
)

# Email address used as sender (From field).
SERVER_EMAIL = "no-reply@cloudml.int.odesk.com"

# Mailserver configuration
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""


try:
    from api.local_config import *
except ImportError:
    pass
