SECRET_KEY = 'CHANGE_ME'
#SQLALCHEMY_DATABASE_URI = 'sqlite:///cloudml.db'
DATABASE_NAME = 'main_cloudml'
STATIC_ROOT = None
UPLOAD_FOLDER = 'models'
MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = True

# Celery specific settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
#BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
BROKER_URL = 'mongodb://localhost:27017/cloudmlqueue'
CELERY_RESULT_BACKEND = ''
CELERY_IMPORTS = ('api.models', 'api', 'api.tasks')