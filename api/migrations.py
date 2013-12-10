import sys
import inspect

from mongokit import DocumentMigration

import models
from . import app


class DbMigration(DocumentMigration):
    DOC_CLASS = None

    def __init__(self):
        super(DbMigration, self).__init__(self.DOC_CLASS)

    def migrate_all(self, *args, **kwargs):
        super(DbMigration, self).migrate_all(
            getattr(app.db, self.DOC_CLASS.__collection__))

    @staticmethod
    def get_migrations_module():  # pragma: no cover
        return sys.modules[__name__]

    @classmethod
    def do_all_migrations(cls, class_or_collection=None):
        for name, obj in inspect.getmembers(
                cls.get_migrations_module(), inspect.isclass):
            if hasattr(obj, '__bases__') and cls in obj.__bases__:
                if (not class_or_collection
                    or class_or_collection == obj.DOC_CLASS.__collection__
                        or class_or_collection == obj.DOC_CLASS.__name__):
                    migration = obj()
                    migration.migrate_all()
