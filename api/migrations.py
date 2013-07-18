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
        super(DbMigration, self).migrate_all(getattr(app.db, self.DOC_CLASS.__collection__))

    @classmethod
    def do_all_migrations(cls):
        for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if hasattr(obj, '__bases__') and cls in obj.__bases__:
                obj().migrate_all()


class ModelMigration(DbMigration):
    DOC_CLASS = models.Model

    def allmigration01__add_example_id(self):
        self.target = {'example_id': {'$exists': False}}
        self.update = {'$set': {'example_id': 'application_id'}}

    def allmigration02__add_example_label(self):
        self.target = {'example_label': {'$exists': False}}
        self.update = {'$set': {'example_label': 'contractor.dev_profile_title'}}


class TestMigration(DbMigration):
    DOC_CLASS = models.Test

    def allmigration01__add_model_id(self):
        self.target = {'model_id': {'$exists': False}, 'model': {'$exists': True}}
        if not self.status:
            for doc in self.collection.find(self.target):
                self.update = {'$set': {'model_id': doc.model._id }}
                self.collection.update(self.target, self.update)
