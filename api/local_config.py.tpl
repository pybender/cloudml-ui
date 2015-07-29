SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = 'cloudml://cloudml:cloudml@localhost/cloudml'

MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = True

AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'

CLOUDML_PREDICT_BUCKET_NAME = '{{ amazon_bucket_name }}'

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk api key }}'
ODESK_OAUTH_SECRET = '{{ odesk secret key }}'

LOCAL_DYNAMODB = True
BROKER_URL = 'amqp://cloudml:cloudml@localhost:5672/cloudml';
DYNAMODB_LIBRARY_PATH= '~/dynamodb/DynamoDBLocal_lib'
DYNAMODB_JAR= '~/dynamodb/DynamoDBLocal.jar'
