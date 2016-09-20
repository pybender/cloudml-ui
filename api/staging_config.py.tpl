from datetime import timedelta

SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = '{{ database_uri }}'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
DATA_FOLDER = '{{ current_var_link }}/data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024

#GRAFANA_KEY = "eyJrIjoiYk1KME10bGtOSGh2V3JZVmxFWlJIU0ljcnFLRzE5OTUiLCJuIjoibmlrb2xheW1lbG5payIsImlkIjoxfQ=="
GRAFANA_KEY = "eyJrIjoibXllRFY3M2JkcjMyd25sWjdaZ1pYSEM2MEh4eldsd3kiLCJuIjoibm1lbG5payIsImlkIjoxfQ=="
GRAFANA_HOST = "grafana.odesk.com"

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
BROKER_URL = 'amqp://cloudml:cloudml@localhost:5672/cloudml'
CELERY_RESULT_BACKEND = 'amqp://cloudml:cloudml@localhost:5672/cloudml'

CELERY_IMPORTS = (
    'api.models', 'api', 'api.import_handlers.tasks',
    'api.instances.tasks', 'api.ml_models.tasks',
    'api.model_tests.tasks', 'api.servers.tasks')

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = [
    Queue('default', routing_key='task.#')
]
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'
CELERYD_MAX_TASKS_PER_CHILD = 1
CELERYBEAT_SCHEDULE = {
    'add-every-week': {
        'task': 'api.ml_models.tasks.models.clear_model_data_cache',
        'schedule': timedelta(days=7)
    },
}


AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'

CLOUDML_PREDICT_BUCKET_NAME = '{{ amazon_bucket_name }}'

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk_api_key }}'
ODESK_OAUTH_SECRET = '{{ odesk_secret_key }}'
#ODESK_API_URL = 'https://stage.upwork.com'

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
        'boto3': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': True,
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': True,
        },
        'placebo': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    }
}

MODIFY_DEPLOYED_MODEL = True
MODIFY_DEPLOYED_IH = True
