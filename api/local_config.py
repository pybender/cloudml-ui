SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = '{{ fill me }}'

MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = True

AMAZON_ACCESS_TOKEN = '{{ fill me }}'
AMAZON_TOKEN_SECRET = '{{ fill me }}'
AMAZON_BUCKET_NAME = '{{ fill me }}'
GRAFANA_KEY = "{{ fill me }}"
GRAFANA_HOST = "{{ fill me }}"

CLOUDML_PREDICT_BUCKET_NAME = 'pnvaskocloudml'

DYNAMODB_PATH = '/media/wwwnfs/upwork/cloudml'

# OAuth keys
ODESK_OAUTH_KEY = '{{ fill me }}'
ODESK_OAUTH_SECRET = '{{ fill me }}'

LOCAL_DYNAMODB = True

MODIFY_DEPLOYED_MODEL = True
MODIFY_DEPLOYED_IH = False

# Modify Import handler after deployed to AWS
# Example MODIFY_DEPLOYED: {'Production':(edit, delete)}; 1 - enable, 0 - disable

MODIFY_DEPLOYED ={'Production': (0, 0),
                  'Staging': (1, 0),
                  'Analytics': (1, 0),
                  'Development': (1, 1)
                  }
