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
    def do_all_migrations(cls, class_or_collection=None):
        for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if hasattr(obj, '__bases__') and cls in obj.__bases__:
                if (not class_or_collection
                    or class_or_collection == obj.DOC_CLASS.__collection__
                        or class_or_collection == obj.DOC_CLASS.__name__):
                    migration = obj()
                    migration.migrate_all()


class ModelMigration(DbMigration):
    DOC_CLASS = models.Model

    def allmigration01__add_example_id(self):
        self.target = {'example_id': {'$exists': False}}
        self.update = {'$set': {'example_id': 'application_id'}}

    def allmigration02__add_example_label(self):
        self.target = {'example_label': {'$exists': False}}
        self.update = {'$set': {'example_label': 'contractor.dev_profile_title'}}

    def allmigration04__add_tests_count(self):
        self.target = {'tests_count': {'$exists': False}}
        if not self.status:
            for doc in self.collection.find(self.target):
                tests_count = app.db.Test.find({'model_id': str(doc['_id'])}).count()
                self.update = {'$set': {'tests_count': tests_count}}
                target = self.target.copy()
                target['_id'] = doc['_id']
                self.collection.update(target, self.update)


class TestMigration(DbMigration):
    DOC_CLASS = models.Test

    def allmigration01__add_model_id(self):
        self.target = {'model_id': {'$exists': False}, 'model': {'$exists': True}}
        if not self.status:
            for doc in self.collection.find(self.target):
                self.update = {'$set': {'model_id': doc.model._id }}
                self.collection.update(self.target, self.update)


class DataSetMigration(DbMigration):
    DOC_CLASS = models.DataSet

    def allmigration01__add_stats_fields(self):
        self.target = {
            'filesize': {'$exists': False},
            'records_count': {'$exists': False},
            'time': {'$exists': False},
        }
        self.update = {'$set': {
            'filesize': long(0.0),
            'records_count': 0,
            'time': 0,
        }}
