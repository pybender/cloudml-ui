# Authors: Nikolay Melnik <nmelnik@upwork.com>

import os
import logging

from flask.ext.script import Manager, Command, Shell, Option
from flask.ext.migrate import Migrate, MigrateCommand

from api import app
import boto.ec2


class CreateWorkerImage(Command):
    """Create worker image."""
    def get_options(self):
        return (
            Option('-v', '--version',
                   dest='version',
                   default='cloudml-worker.v3.0',
                   help='For example cloudml-worker.v3.0'),
        )

    def run(self, **kwargs):
        version = kwargs.get('version')
        token = app.config['AMAZON_ACCESS_TOKEN']
        secret = app.config['AMAZON_TOKEN_SECRET']
        conn = boto.ec2.connect_to_region(
            'us-west-2',
            aws_access_key_id=token,
            aws_secret_access_key=secret)
        inst = conn.get_all_instances(instance_ids=['i-49a0597d'])
        image = inst[0].instances[0].create_image(version)
        print "Created image: %s" % image


class Celeryd(Command):
    """Runs a Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.tasks worker --concurrency=10 -Q default -E --loglevel=info")


class Celeryw(Command):
    """Runs a Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.tasks worker --concurrency=10 -Q worker1 -E --loglevel=info")


class Flower(Command):
    """Runs a Celery Flower worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.tasks flower --loglevel=info")


class Run(Command):
    """Runs a Celery Flower worker node."""

    def run(self, **kwargs):
        import gevent.monkey
        from gevent.pywsgi import WSGIServer
        gevent.monkey.patch_all()
        http_server = WSGIServer(('', 5000), app)
        http_server.serve_forever()


def _make_context():
    from api import models
    return dict(app=app, db=app.sql_db, models=models)


class Test(Command):
    """
    Run app tests.
    Please initialize env variable with path to test config:

    $ export CLOUDML_CONFIG="{{ path to }}/cloudml-ui/api/test_config.py"
    """

    def get_options(self):
        return (
            Option('-t', '--tests',
                   dest='tests',
                   default=None,
                   help="specifies tests"),
        )

    def run(self, **kwargs):
        import nose
        app.config.from_object('api.test_config')
        app.init_db()
        argv = ['--with-coverage', '--verbose']
        tests = kwargs.get('tests', None)
        if tests:
            argv.append('--tests')
            argv.append(tests)
        try:
            logging.debug("Running nosetests with args: %s", argv)
            nose.run(argv=argv)
        finally:
            if app.config['SQLALCHEMY_DATABASE_URI'].endswith('test_cloudml'):
                logging.debug(
                    "drop tables (%s)", app.config['SQLALCHEMY_DATABASE_URI'])
                app.sql_db.session.remove()
                app.sql_db.drop_all()


class Coverage(Command):
    """Build test code coverage report."""

    def run(self):
        import nose
        print 'Collecting coverage info...'
        output_dir = 'coverage'
        args = [
            'with-coverage',
            'verbose',
            'cover-erase',
            'cover-html',
            'cover-package=api',
            "cover-html-dir={0}".format(output_dir),
        ]
        os.system('nosetests --{0}'.format(' --'.join(args)))
        # nose.run(argv=['', ] + ['--{}'.format(arg) for arg in args])
        report_path = 'file://' + os.path.join(
            os.path.abspath(output_dir), 'index.html')
        print 'Coverage html report has been generated at {}'.format(
            report_path)


class RemPycFiles(Command):
    CMD = 'find . -name "*.pyc" -exec rm -rf {} \;'

    def run(self):
        os.system(self.CMD)


class CreateDbTables(Command):
    """Create db tables"""

    def run(self, **kwargs):
        app.sql_db.create_all()
        print 'Done.'


class CreateDynamoDbTables(Command):
    """Create db tables"""

    def run(self, **kwargs):
        from api.logs.dynamodb.models import LogMessage
        from api.accounts.models import AuthToken
        LogMessage.create_table()
        AuthToken.create_table()
        print 'Done.'


class DropDbTables(Command):
    """Drop db tables"""

    def run(self, **kwargs):
        app.sql_db.drop_all()
        print 'Dropped.'


class GenerateCrc(Command):
    def run(self, **kwargs):
        import zlib
        from api.amazon_utils import AmazonS3Helper
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        for key in s3.list_keys('staging/importhandlers/'):
            print key.name
            data = s3.load_key(key.name)
            crc32 = '0x%08X' % (zlib.crc32(data) & 0xffffffff)
            try:
                s3.set_key_metadata(key.name, {'crc32': crc32}, False)
            except:
                print 'Error'


manager = Manager(app)
migrate = Migrate(app, app.sql_db)
manager.add_command('db', MigrateCommand)
manager.add_command("celeryd", Celeryd())
manager.add_command("celeryw", Celeryw())
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command('generate_crc', GenerateCrc())
manager.add_command('coverage', Coverage())
manager.add_command('run', Run())
manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("create_db_tables", CreateDbTables())
manager.add_command("create_dynamodb_tables", CreateDynamoDbTables())
manager.add_command("drop_db_tables", DropDbTables())
manager.add_command("rem_pyc", RemPycFiles())
manager.add_command("create_image", CreateWorkerImage())


if __name__ == "__main__":
    manager.run()
