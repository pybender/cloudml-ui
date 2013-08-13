SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{{ current_var_link }}/cloudml.db'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
DATA_FOLDER = '{{ current_var_link }}/data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DATABASE_NAME = 'cloudml'
DATABASE_HOST = '172.27.77.252'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
#BROKER_URL = 'sqla+sqlite:////home/cloudml/shared/var/cloudml-celery.db'
BROKER_URL = 'amqp://cloudml:cloudml@localhost:5672/cloudml'
CELERY_RESULT_BACKEND = 'amqp://cloudml:cloudml@localhost:5672/cloudml'

CELERY_IMPORTS = ('api.models', 'api', 'api.tasks')

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = [
    Queue('default', routing_key='task.#')
]
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk api key }}'
ODESK_OAUTH_SECRET = '{{ odesk secret key }}'

REQUESTING_INSTANCE_COUNTDOWN = 20
REQUESTING_INSTANCE_MAX_RETRIES = 30

EXAMPLES_CHUNK_SIZE = 10
MAX_MONGO_EXAMPLE_SIZE = 2000

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
