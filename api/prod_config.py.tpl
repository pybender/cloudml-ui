SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = '{{ database_uri }}'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
DATA_FOLDER = '{{ current_var_link }}/data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
TEST_MODE = False

GRAFANA_KEY = "eyJrIjoiYk1KME10bGtOSGh2V3JZVmxFWlJIU0ljcnFLRzE5OTUiLCJuIjoibmlrb2xheW1lbG5payIsImlkIjoxfQ=="
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

AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'

CLOUDML_PREDICT_BUCKET_NAME = '{{ amazon_bucket_name }}'

MULTIPART_UPLOAD_CHUNK_SIZE = 8192

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk_api_key }}'
ODESK_OAUTH_SECRET = '{{ odesk_secret_key }}'

REQUESTING_INSTANCE_COUNTDOWN = 20
REQUESTING_INSTANCE_MAX_RETRIES = 30

EXAMPLES_CHUNK_SIZE = 10

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = True
SEND_ERROR_EMAILS = True

ADMINS = (
    ("Nikolay Melnik", "nmelnik@upwork.com"),
    ("Nader Soliman", "nsoliman@upwork.com"),
)

# Email address used as sender (From field).
SERVER_EMAIL = '{{ server_email }}'

# Mailserver configuration
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""

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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'normal'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'boto': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

MODIFY_DEPLOYED_MODEL = False
MODIFY_DEPLOYED_IH = False