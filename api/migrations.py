import sys
import inspect
import json

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

    # def allmigration01__add_example_id(self):
    #     self.target = {'example_id': {'$exists': False}}
    #     self.update = {'$set': {'example_id': 'application_id'}}

    def allmigration02__add_example_label(self):
        self.target = {'example_label': {'$exists': False}}
        self.update = {'$set': {'example_label': 'contractor.dev_profile_title'}}

    def allmigration03__add_memory_usage(self):
        self.target = {'memory_usage': {'$exists': False}}
        self.update = {'$set': {'memory_usage': {}}}


class TestMigration(DbMigration):
    DOC_CLASS = models.Test

    # def allmigration01__add_model_id(self):
    #     self.target = {'model_id': {'$exists': False}, 'model': {'$exists': True}}
    #     if not self.status:
    #         for doc in self.collection.find(self.target):
    #             self.update = {'$set': {'model_id': doc.model._id }}
    #             self.collection.update(self.target, self.update)

    def allmigration02__add_exports(self):
        self.target = {'exports': {'$exists': False}}
        self.update = {'$set': {'exports': []}}


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

    def allmigration02__add_data_fields(self):
        self.target = {'data_fields': {'$exists': False}}
        self.update = {'$set': {'data_fields': []}}

    def allmigration03__fill_data_fields(self):
        self.target = {
            'data_fields': {'$size': 0}
        }
        if not self.status:
            for doc in self.collection.find(self.target):
                dataset = app.db.DataSet.find_one({'_id': doc['_id']})
                row = None
                try:
                    with dataset.get_data_stream() as fp:
                        row = next(fp)
                    if row:
                        dataset.data_fields = json.loads(row).keys()
                        dataset.save()
                except Exception, e:
                    print e
