SECRET_KEY = 'CHANGE_ME'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
DATA_FOLDER = '{{ current_var_link }}/data'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DATABASE_NAME = 'cloudml'
DATABASE_HOST = '172.27.77.252'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
BROKER_URL = 'amqp://cloudml:cloudml@172.27.77.141:5672/cloudml'
CELERY_RESULT_BACKEND = 'amqp://cloudml:cloudml@172.27.77.141:5672/cloudml'

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

EXAMPLES_CHUNK_SIZE = 10
MAX_MONGO_EXAMPLE_SIZE = 2000

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk_api_key }}'
ODESK_OAUTH_SECRET = '{{ odesk_secret_key }}'

REQUESTING_INSTANCE_COUNTDOWN = 20
REQUESTING_INSTANCE_MAX_RETRIES = 30

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

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = True
SEND_ERROR_EMAILS = False

# Name and email addresses of recipients
ADMINS = (
    ("Nikolay Melnik", "nmelnik@odesk.com"),
    ("Mikhail Medvedev", "moorcock@odesk.com"),
)

# Email address used as sender (From field).
SERVER_EMAIL = "{{ server_email }}"

# Mailserver configuration
EMAIL_HOST = "{{ smtp_server_address }}"
EMAIL_PORT = {{ smtp_server_port }}
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
