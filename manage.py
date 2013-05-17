import os

from flask.ext.script import Manager, Command, Shell

from api import app

import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()


class Celeryd(Command):
    """Runs a Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.celery worker -E --loglevel=info")


class Flower(Command):
    """Runs a Celery Flower worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.celery flower --loglevel=info")

class Run(Command):
    """Runs a Celery Flower worker node."""

    def run(self, **kwargs):
        http_server = WSGIServer(('', 5000), app)
        http_server.serve_forever()

class Migrate(Command):
    """Migrate"""

    def run(self, **kwargs):
        from api.migrations import ModelMigration
        from api.models import Model
        ModelMigration(Model).migrate_all(app.db.Model.collection)


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
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command('migrate', Migrate())
manager.add_command('run', Run())
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
