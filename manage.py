import os

from flask.ext.script import Manager, Command, Shell, Option

import logging
from bson.objectid import ObjectId
from mongokit.mongo_exceptions import AutoReferenceError
from flask.ext.migrate import Migrate, MigrateCommand

import api
app = api.app


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


class MongoMigrate(Command):
    """Migrate"""

    def get_options(self):
        return (
            Option('-d', '--document',
                   dest='document',
                   default=None),
        )

    def run(self, **kwargs):
        from api.migrations import DbMigration
        DbMigration.do_all_migrations(kwargs.get('document'))


def _make_context():
    from api import models
    return dict(app=app, db=app.db, models=models)


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
                logging.debug("drop tables (%s)", app.config['SQLALCHEMY_DATABASE_URI'])
                app.sql_db.session.remove()
                app.sql_db.drop_all()

            if app.db.name == 'cloudml-test-db':
                logging.debug("remove mongo collections from db: %s", app.db.name)
                for name in app.db.collection_names():
                    if not name.startswith('system.'):
                        model = getattr(app.db, name)
                        model.drop()


class Coverage(Command):
    """Build test code coverage report."""

    def run(self):
        import nose
        app.config.from_object('api.test_config')
        app.init_db()
        print 'Collecting coverage info...'
        output_dir = 'api/test/cover'
        # TODO: why does nose.run show different results?
        # nose.run(argv=[
        #     '',
        #     '--with-coverage', '--cover-erase', '--cover-html',
        #     '--cover-html-dir={}'.format(output_dir),
        #     '--cover-package=api'])
        args = [
            'with-coverage',
            # 'with-xcoverage',
            'cover-erase',
            'cover-html',
            'cover-package=api',
            # 'with-xunit',
            # "xunit-file={0}/report.xml".format(output_dir),
            "cover-html-dir={0}".format(output_dir),
            #"xcoverage-file={0}/coverage.xml".format(output_dir),
        ]
        # os.system('nosetests --{0}'.format(' --'.join(args)))
        nose.run(argv=['', ] + ['--{}'.format(arg) for arg in args])
        report_path = 'file://' + os.path.join(
            os.path.abspath(output_dir), 'index.html')
        print 'Coverage html report has been generated at {}'.format(
            report_path)


class RemPycFiles(Command):
    CMD = 'find . -name "*.pyc" -exec rm -rf {} \;'

    def run(self):
        os.system(self.CMD)


class RemObsoluteMongoKeys(Command):
    """
    Removes obsolete (hung ups) Tests, Examples, Logs, etc. from
    mongodb.
    """
    TYPE_CHOICES = ('models', 'tests')

    option_list = (
        Option('--obj', '-o', dest='obj_type', default='all'),
    )

    def run(self, obj_type):
        def execute(obj_type):
            mthd = getattr(self, "_check_%s" % obj_type)
            err_count = mthd()
            if err_count:
                logging.error('Executed with %d errors', err_count)
            else:
                logging.info('Executed without errors!')

        if obj_type != 'all':
            execute(obj_type)
        else:
            for obj_type in self.TYPE_CHOICES:
                execute(obj_type)

    def _check_models(self):
        logging.info("================ Analyse Models ================")
        for i, model in enumerate(app.db.Model.find()):
            logging.info('%d - Model: %s', i, model.name)

            def _check_handler(handler_type='test'):
                hander = model.get('%s_import_handler' % handler_type)
                if not hander:
                    logging.warning('%s Handler not set', handler_type)

            _check_handler('test')
            _check_handler('train')

            train_handler_dict = model.get('train_importhandler')
            if train_handler_dict:
                logging.warning('Train import handler dict is here!')

            importhandler_dict = model.get('importhandler')
            if importhandler_dict:
                logging.warning('Test import handler dict is here!')

    def _check_tests(self):
        logging.info("================ Analyse Tests ================")
        fields = ('name', '_id', 'model_name',
                  'model_id', 'created_on')
        err_count = 0
        for i, test in enumerate(app.db.Test.find({}, fields)):
            model_name = test.get('model_name', None)
            model_id = test.get('model_id', None)
            logging.info("%d - Test: %s. Created: %s", i, test._id, test.created_on)
            logging.info('Looking for model by id')
            err_count += self._look_model_by_id('Model', _id=model_id)
            logging.info('Looking for model by name')
            err_count += self._look_model_by_id('Model', name=model_name)

            test_obj = None
            try:
                test_obj = app.db.Test.find_one({'_id': test._id})
                if test_obj.status == app.db.Test.STATUS_ERROR:
                    logging.warning('Test executed with error %s', test_obj.error)
                if test_obj.status == app.db.Test.STATUS_QUEUED:
                    logging.warning('Test is queued. Please check whether it isn"t hung ups.')
            except AutoReferenceError, exc:
                err_count += 1
                logging.error('Problem with db refs: %s', exc)

            if test_obj:
                ds = test_obj.get('dataset', None)
                if ds:
                    logging.info('Dataset found %s', ds.name)
                else:
                    logging.warning('DataSet not set')

        return err_count

    def _check_logs(self):
        logging.info("================ Analyse Logs ================")
        err_count = 0

        def _check(log, err_count, name):
            err_count = 0
            if log.params.keys() != ['obj']:
                logging.info('Log created %s', log.get('created_on'))
                logging.error('Invalid parameters: %s', log.params)
                err_count += 1
            else:
                _id = log.params['obj']
                Model = getattr(app.db, name)
                obj = Model.find({'_id': ObjectId(_id)})
                if not obj:
                    logging.error('%s not found by id: %s', name, _id)
                    err_count += 1
            return err_count

        for i, log in enumerate(app.db.LogMessage.find()):
            # TODO: Fix issue with not set created on!
            # if not log.get('created_on'):
            #     logging.warning('Created on not set')

            if log.type == app.db.LogMessage.TRAIN_MODEL:
                err_count += _check(log, err_count, 'Model')
            elif log.type == app.db.LogMessage.IMPORT_DATA:
                err_count += _check(log, err_count, 'DataSet')
            elif log.type == app.db.LogMessage.RUN_TEST:
                err_count += _check(log, err_count, 'Test')
            elif log.type == app.db.LogMessage.CONFUSION_MATRIX_LOG:
                err_count += _check(log, err_count, 'Test')
            else:
                logging.error('Invalid type %s', log.type)
                err_count += 1

        return err_count

    def _check_examples(self):
        logging.info("================ Analyse Test Examples ================")
        err_count = 0
        for i, example in enumerate(app.db.TestExamples.find()):
            test = example.test
            if not test:
                logging.error('Test not found for example %s', example._id)
                err_count += 1
            err_count += self._look_model_by_id('Model', _id=test.model_id)
            err_count += self._look_model_by_id('Model', name=test.model_name)
            err_count += self._look_model_by_id('Test', _id=test.test_id)
            err_count += self._look_model_by_id('Test', name=test.test_name)
        return err_count

    def _look_model_by_id(self, model_name='Model', **kwargs):
        err_count = 0
        for key, val in kwargs.iteritems():
            if not val:
                logging.warning('%s not set', key)
                return err_count

            if key == '_id':
                kwargs['_id'] = ObjectId(val)

            MODEL = getattr(app.db, model_name)
            model = MODEL.find_one(kwargs)
            if not model:
                logging.error('%s not found by %s', model_name, kwargs)
                err_count += 1
            else:
                logging.info('Found: %s', model.name)
        return err_count


class CreateDbTables(Command):
    """Create db tables"""

    def run(self, **kwargs):
        app.sql_db.create_all()
        print 'Done.'


class DropDbTables(Command):
    """Drop db tables"""

    def run(self, **kwargs):
        app.sql_db.drop_all()
        print 'Dropped.'


class MigrateToPosgresql(Command):
    def run(self, **kwargs):
        from api.mongo.migrator import migrate as pmigrate
        pmigrate()
        print 'Done.'


manager = Manager(app)
migrate = Migrate(app, app.sql_db)
manager.add_command('db', MigrateCommand)
manager.add_command("celeryd", Celeryd())
manager.add_command("celeryw", Celeryw())
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command('coverage', Coverage())
manager.add_command('migrate', MongoMigrate())
manager.add_command('run', Run())
manager.add_command('fix_mongo', RemObsoluteMongoKeys())
manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("create_db_tables", CreateDbTables())
manager.add_command("drop_db_tables", DropDbTables())
manager.add_command("migrate_to_postgresql", MigrateToPosgresql())
manager.add_command("rem_pyc", RemPycFiles())

if __name__ == "__main__":
    manager.run()
