DATABASE_NAME = 'cloudml-test-db'
DATA_FOLDER = 'test_data'

DB_NAME = 'test_db'
DB_FORMAT_URI = 'postgresql://postgres:postgres@localhost/%s'
SQLALCHEMY_DATABASE_URI = DB_FORMAT_URI % DB_NAME

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = False

TEST_DYNAMODB = True
#LOCAL_DYNAMODB = True