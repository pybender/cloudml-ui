from api import celery
celery.conf['CELERY_ALWAYS_EAGER'] = True
celery.conf['CELERY_EAGER_PROPAGATES_EXCEPTIONS'] = False
