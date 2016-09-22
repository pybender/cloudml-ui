SECRET_KEY = 'CHANGE_ME'
SQLALCHEMY_DATABASE_URI = 'postgresql://cloudml:cloudml@192.168.2.253/cloudml'

MAX_CONTENT_LENGTH = 128 * 1024 * 1024
DEBUG = True

AMAZON_ACCESS_TOKEN = 'AKIAIUWUPRAV4UJJMGZQ'
AMAZON_TOKEN_SECRET = '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'
AMAZON_BUCKET_NAME = 'pnvaskocloudml'
GRAFANA_KEY = "{{ fill me }}"
GRAFANA_HOST = "{{ fill me }}"

CLOUDML_PREDICT_BUCKET_NAME = 'pnvaskocloudml'

DYNAMODB_PATH = '/media/wwwnfs/upwork/cloudml'

# OAuth keys
ODESK_OAUTH_KEY = '2833be966d0b00a70d1a2079e614ea24'
ODESK_OAUTH_SECRET = '799cdf747b6889a0'

LOCAL_DYNAMODB = True

MODIFY_DEPLOYED_MODEL = True
MODIFY_DEPLOYED_IH = False
MODIFY_DEPLOYED ={'Production': (0, 0),
                  'Staging': (1, 0),
                  'Analytics': (1, 0),
                  'Development': (1, 1)
                  }
