SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{{ active_var_link }}/cloudml.db'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DATABASE_NAME = 'cloudml'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
#BROKER_URL = 'sqla+sqlite:////home/cloudml/shared/var/cloudml-celery.db'
BROKER_URL = 'amqp://cloudml:cloudml@localhost:5672/cloudml'
CELERY_RESULT_BACKEND = ''