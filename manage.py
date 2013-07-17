import os

from flask.ext.script import Manager, Command, Shell, Option

import logging
from bson.objectid import ObjectId
from mongokit.mongo_exceptions import AutoReferenceError

from api import app


class Celeryd(Command):
    """Runs a Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.tasks worker -Q default -E --loglevel=info")


class Celeryw(Command):
    """Runs a Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.tasks worker -Q worker1 -E --loglevel=info")


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


class Migrate(Command):
    """Migrate"""

    def run(self, **kwargs):
        from bson.objectid import ObjectId
        from bson.dbref import DBRef

        model_collection = app.db.Model.collection
        model_list = model_collection.find({})

        def _update(doc, fieldname, collection):
            if fieldname in doc:
                val = doc[fieldname]
                if val and isinstance(val, dict):
                    _id = val['_id']
                    doc[fieldname] = DBRef(collection=collection,
                                           id=ObjectId(_id),
                                           database=app.config['DATABASE_NAME'])

        print "Adding dbrefs"
        for model in model_list:
            _update(model, "test_import_handler", "handlers")
            _update(model, "train_import_handler", "handlers")
            _update(model, "dataset", "dataset")
            model['feature_count'] = -1
            model_collection.save(model)
            print 'Model %s was updated' % model['name']

        print "Recalc features count"
        for model in app.db.Model.find({}):
            trainer = model.get_trainer()
            model.feature_count = len(trainer._feature_model.features.keys())
            model.save()
            print 'Model %s has %s features' % (model.name, model.feature_count)


def _make_context():
    from api import models
    return dict(app=app, db=app.db, models=models)


class Test(Command):
    """Run app tests."""

    def run(self):
        import nose
        nose.run(argv=['', '--exclude-dir=core'])


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
            mthd()

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
        for i, test in enumerate(app.db.Test.find({}, fields)):
            model_name = test.get('model_name', None)
            model_id = test.get('model_id', None)
            logging.info("%d - Test: %s. Created: %s", i, test._id, test.created_on)
            logging.info('Looking for model by id')
            if model_id:
                model = app.db.Model.find_one({'_id': ObjectId(model_id)})
                if not model:
                    logging.error('Model not found by id %s' % model_id)
                else:
                    logging.info('Found: %s', model.name)
            else:
                logging.warning('Model id not set.')

            logging.info('Looking for model by name')
            if model_name:
                model = app.db.Model.find_one({'name': model_name})
                if not model:
                    logging.error('Model not found by name %s' % model_name)
                else:
                    logging.info('Found: %s', model.name)
            else:
                logging.warning('Model name not set.')

            test_obj = None
            try:
                test_obj = app.db.Test.find_one({'_id': test._id})
                if test_obj.status == app.db.Test.STATUS_ERROR:
                    logging.warning('Test executed with error %s', test_obj.error)
                if test_obj.status == app.db.Test.STATUS_QUEUED:
                    logging.warning('Test is queued. Please check whether it isn"t hung ups.')
            except AutoReferenceError, exc:
                logging.error('Problem with db refs: %s', exc)

            if test_obj:
                ds = test_obj.get('dataset', None)
                if ds:
                    logging.info('Dataset found %s', ds.name)
                else:
                    logging.warning('DataSet not set')

            # Analyse Logs

manager = Manager(app)
manager.add_command("celeryd", Celeryd())
manager.add_command("celeryw", Celeryw())
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command('migrate', Migrate())
manager.add_command('run', Run())
manager.add_command('fix_mongo', RemObsoluteMongoKeys())
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
