import os

from flask.ext.script import Manager, Command, Shell

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


manager = Manager(app)
manager.add_command("celeryd", Celeryd())
manager.add_command("celeryw", Celeryw())
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command('migrate', Migrate())
manager.add_command('run', Run())
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
