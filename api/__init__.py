"""
This module main application class and gather all imports together.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
from logging import config as logging_config

from flask.ext.admin import Admin
from celery import Celery

from app import create_app
from rest_api import Api

app = create_app()
celery = Celery('cloudml')
celery.add_defaults(lambda: app.config)

api = Api(app)
admin = Admin(app, 'CloudML Admin Interface')

logging_config.dictConfig(app.config['LOGGING'])

# Note: to see sqlalchemy SQL statements, uncomment the following,
# and watch out for the logs will be huge
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

if app.config.get('SEND_ERROR_EMAILS'):
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        mailhost=(app.config['EMAIL_HOST'], app.config['EMAIL_PORT']),
        fromaddr=app.config['SERVER_EMAIL'],
        toaddrs=[email for name, email in app.config['ADMINS']],
        subject='Cloud ML Error',
        credentials=(
            app.config['EMAIL_HOST_USER'], app.config['EMAIL_HOST_PASSWORD'])
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

APPS = ('accounts', 'features', 'import_handlers', 'instances',
        'logs', 'ml_models', 'model_tests', 'statistics', 'reports',
        'async_tasks', 'servers')


def importer(app_name):
    def imp(name):
        try:
            __import__(name)
        except ImportError, exc:
            exc_msg = str(exc)
            mod = name.split('.')[2]
            if exc_msg.startswith('No module named') and mod in exc_msg:
                return False
            raise
        else:
            return True
    imp('api.%s.admin' % app_name)
    imp('api.%s.models' % app_name)
    imp('api.%s.views' % app_name)

for app_name in APPS:
    importer(app_name)
