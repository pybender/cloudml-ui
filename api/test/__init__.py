from api import celery
celery.conf['CELERY_ALWAYS_EAGER'] = True
