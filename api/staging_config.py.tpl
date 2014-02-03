SECRET_KEY = 'CHANGE_ME'
#SQLALCHEMY_DATABASE_URI = 
#'sqlite:////webapps/cloudml/shared/var/cloudml.db'
SQLALCHEMY_DATABASE_URI = 'postgresql://cloudml:W0y137OY@odesk-cloudml-staging.cw38fhqllwnc.us-west-1.rds.amazonaws.com/cloudml_staging'

STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DATABASE_NAME = 'cloudml'
DATABASE_HOST = '172.27.77.252'
DATA_FOLDER = '{{ current_var_link }}/data'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
#BROKER_URL = 'sqla+sqlite:////home/cloudml/shared/var/cloudml-celery.db'
BROKER_URL = 'amqp://cloudml:cloudml@localhost:5672/cloudml'
CELERY_RESULT_BACKEND = 'amqp://cloudml:cloudml@localhost:5672/cloudml'


CELERY_IMPORTS = (
    'api.models', 'api', 'api.import_handlers.tasks',
    'api.instances.tasks', 'api.ml_models.tasks',
    'api.model_tests.tasks')

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = [
    Queue('default', routing_key='task.#')
]
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'
CELERYD_MAX_TASKS_PER_CHILD = 1


AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'

CLOUDML_PREDICT_FOLDER_MODELS = 'predict/models'

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk_api_key }}'
ODESK_OAUTH_SECRET = '{{ odesk_secret_key }}'

MULTIPART_UPLOAD_CHUNK_SIZE = 8192

REQUESTING_INSTANCE_COUNTDOWN = 20
REQUESTING_INSTANCE_MAX_RETRIES = 30

EXAMPLES_CHUNK_SIZE = 10

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = True
SEND_ERROR_EMAILS = True

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
