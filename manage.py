# Authors: Nikolay Melnik <nmelnik@upwork.com>

import os
import logging
import boto3
from flask.ext.script import Manager, Command, Shell, Option
from flask.ext.migrate import Migrate, MigrateCommand

from api import app


class CreateWorkerImage(Command):
    """
    Creates Amazon EC2 instance with preinstalled
    Cloudml celery worker to use it in the spot instance.
    """
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
        conn = boto3.resource('ec2',
                              region_name='us-west-2',
                              aws_access_key_id=token,
                              aws_secret_access_key=secret)
        inst = conn.Instance('i-49a0597d')
        image = inst.create_image(Name=version)
        print "Created image: %s" % image


class Celeryd(Command):
    """Runs the default Celery worker node."""

    def run(self, **kwargs):
        os.system("env CELERYD_FSNOTIFY=stat celery -A api.tasks worker --autoreload --concurrency=10 -Q default -E --loglevel=info")


class Celeryw(Command):
    """Runs another Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.tasks worker --concurrency=10 -Q worker1 -E --loglevel=info")


class Flower(Command):
    """
    Runs the Celery Flower is a real-time web based monitor
    and administration tool for Celery.
    """

    def run(self, **kwargs):
        os.system("celery -A api.tasks flower --loglevel=info")


def _make_context():
    from api import models
    return dict(app=app, db=app.sql_db, models=models)


class Test(Command):
    """
    Run app tests.

    Be carefull: don't forgot to create test_config.py file
    from template in the api folder.
    """

    def get_options(self):
        return (
            Option('-t', '--tests',
                   dest='tests',
                   default=None,
                   help="specifies unittests to run"),
            Option('-c', '--coverage',
                   dest='coverage',
                   default=None,
                   action='store_true',
                   help="runs API part unittest with coverage")
        )

    def run(self, **kwargs):
        import nose
        app.config.from_object('api.test_config')
        app.init_db()
        #app.sql_db.create_all()
        output_dir = 'coverage'
        argv = ['api', '--verbose']

        coverage = kwargs.get('coverage', None)
        if coverage:
            argv += ['--with-coverage',
                     '--cover-erase',
                     '--cover-html',
                     '--cover-package=api',
                     "--cover-html-dir={0}".format(output_dir)]
        tests = kwargs.get('tests', None)
        if tests:
            argv.append('--tests')
            argv.append(tests)
        try:
            logging.info("Running nosetests with args: %s", argv)
            nose.run(argv=argv)
        finally:
            if app.config['SQLALCHEMY_DATABASE_URI'].endswith('test_cloudml'):
                logging.debug(
                    "drop tables (%s)", app.config['SQLALCHEMY_DATABASE_URI'])
                app.sql_db.session.remove()
                app.sql_db.drop_all()


class CreateDbTables(Command):
    """Create db tables"""

    def run(self, **kwargs):
        app.sql_db.create_all()
        print 'Done.'


class CreateDynamoDbTables(Command):
    """Create tables in DynamoDB (logs, auth)"""

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
            data = s3.load_key(key.name)
            crc32 = '0x%08X' % (zlib.crc32(data) & 0xffffffff)
            try:
                s3.set_key_metadata(key.name, {'crc32': crc32}, False)
            except:
                print 'Error'


class ClearLocalCache(Command):
    """Clear local cache of datasets"""
    def get_options(self):
        return (
            Option('-s', '--show',
                   dest='show',
                   default=False,
                   action='store_true',
                   help="Only show"),
            Option('-d', '--date',
                   dest='date',
                   default=None,
                   help="Date")
        )

    def run(self, **kwargs):
        date = kwargs.get('date', None)
        delete = not kwargs.get('show', True)
        from api.import_handlers.models import DataSet
        from os.path import exists
        ds = DataSet.query.filter(
            DataSet.created_on <= date).all()
        for d in ds:
            if d.filename:
                print d.filename
                if delete and exists(d.filename):
                    os.remove(d.filename)
                    print 'deleted'


class RunDynamoDB(Command):
    """Run local DynamoDB"""
    def run(self, **kwargs):
        dynamodb_path = app.config.get('DYNAMODB_PATH', '~')
        os.system("java -Djava.library.path=\
%s/dynamodb/DynamoDBLocal_lib -jar \
%s/dynamodb/DynamoDBLocal.jar -port 8000" 
        % (dynamodb_path, dynamodb_path))


class UpdateDeployed(Command):
    """Updates deployed models and import handlers"""
    def run(self):
        from api.servers.scripts import update_deployed
        update_deployed()
        print "Done"

class CreateGrafanaDashboards(Command):
    """Create grafana dashboard"""
    def run(self):
        from api.servers.scripts import add_grafana_dashboads
        add_grafana_dashboads()
        print "Done"


class RecalculateCounters(Command):
    """Recalculates models tags counters"""
    def run(self):
        from api.ml_models.scripts import recalculate_tags_counters
        recalculate_tags_counters()
        print "Done"


manager = Manager(app)
migrate = Migrate(app, app.sql_db)
manager.add_command('clearlocalcache', ClearLocalCache())
manager.add_command('rundynamodb', RunDynamoDB())
manager.add_command('db', MigrateCommand)
manager.add_command("celeryd", Celeryd())
manager.add_command("celeryw", Celeryw())
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command('generate_crc', GenerateCrc())
manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("create_db_tables", CreateDbTables())
manager.add_command("create_dynamodb_tables", CreateDynamoDbTables())
manager.add_command("drop_db_tables", DropDbTables())
manager.add_command("create_image", CreateWorkerImage())
manager.add_command("update_deployed", UpdateDeployed())
manager.add_command("create_grafana", CreateGrafanaDashboards())
manager.add_command("recalculate_counters", RecalculateCounters())


if __name__ == "__main__":
    manager.run()
