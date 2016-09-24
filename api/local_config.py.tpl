SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = 'postgresql://cloudml:postgres@localhost/cloudml'

MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = True

AMAZON_ACCESS_TOKEN = '{{ amazon_access_token }}'
AMAZON_TOKEN_SECRET = '{{ amazon_token_secret }}'
AMAZON_BUCKET_NAME = '{{ amazon_bucket_name }}'
GRAFANA_KEY = "{{ fill me }}"
GRAFANA_HOST = "{{ fill me }}"

CLOUDML_PREDICT_BUCKET_NAME = '{{ amazon_bucket_name }}'

DYNAMODB_PATH = '{{ path_to_local_dynamodb }}'

# OAuth keys
ODESK_OAUTH_KEY = '{{ odesk api key }}'
ODESK_OAUTH_SECRET = '{{ odesk secret key }}'

LOCAL_DYNAMODB = True

MODIFY_DEPLOYED_MODEL = True
MODIFY_DEPLOYED_IH = True
MODIFY_DEPLOYED_IH = False

# Modify Import handler after deployed to AWS
# Example MODIFY_DEPLOYED: {'Production':(edit, delete)}; 1 - enable, 0 - disable

MODIFY_DEPLOYED ={'Production': (0, 0),
                  'Staging': (1, 0),
                  'Analytics': (1, 0),
                  'Development': (1, 1)
                  }
