import os

from flask.ext.script import Manager, Command, Shell
from flask.ext.alembic import ManageMigrations

from api import app, models


class Celeryd(Command):
    """Runs a Celery worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.celery worker -E --loglevel=info")


class Flower(Command):
    """Runs a Celery Flower worker node."""

    def run(self, **kwargs):
        os.system("celery -A api.celery flower --loglevel=info")


def _make_context():
    return dict(app=app, db=app.db, models=models)

class Test(Command):
    """Run app tests."""

    def run(self):
        import nose
        nose.run(argv=['', '--exclude-dir=core'])


manager = Manager(app)
manager.add_command("migrate", ManageMigrations())
manager.add_command("celeryd", Celeryd())
manager.add_command("flower", Flower())
manager.add_command('test', Test())
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
