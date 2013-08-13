SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = 'sqlite:////webapps/cloudml/shared/var/cloudml.db'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DATABASE_NAME = 'cloudml'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
BROKER_URL = 'sqla+sqlite:////webapps/cloudml/shared/var/cloudml-celery.db'
CELERY_RESULT_BACKEND = ''


AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk api key }}'
ODESK_OAUTH_SECRET = '{{ odesk secret key }}'
