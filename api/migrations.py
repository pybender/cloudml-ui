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

    @staticmethod
    def get_migrations_module():  # pragma: no cover
        return sys.modules[__name__]

    @classmethod
    def do_all_migrations(cls, class_or_collection=None):
        for name, obj in inspect.getmembers(cls.get_migrations_module(), inspect.isclass):
            if hasattr(obj, '__bases__') and cls in obj.__bases__:
                if (not class_or_collection
                    or class_or_collection == obj.DOC_CLASS.__collection__
                        or class_or_collection == obj.DOC_CLASS.__name__):
                    migration = obj()
                    migration.migrate_all()


class ModelMigration(DbMigration):  # pragma: no cover
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

    def allmigration04__add_created_by(self):
        self.target = {'created_by': {'$exists': False}}
        self.update = {'$set': {'created_by': {}}}

    def allmigration05__add_updated_by(self):
        self.target = {'updated_by': {'$exists': False}}
        self.update = {'$set': {'updated_by': {}}}

    def allmigration06__add_trained_by(self):
        self.target = {'trained_by': {'$exists': False}}
        self.update = {'$set': {'trained_by': {}}}

    def allmigration07__move_to_multiple_dataset(self):
        self.target = {'dataset_ids': {'$exists': False}}
        if not self.status:
            for doc in self.collection.find(self.target):
                try:
                    doc['dataset_ids'] = []

                    if doc.get('dataset'):
                        doc['dataset_ids'].append(doc['dataset'].id)
                    elif doc['train_import_handler']:
                        ds = app.db.DataSet.find_one({
                            'import_handler_id': str(
                                doc['train_import_handler'].id),
                            'status': 'Imported'
                        })
                        if ds:
                            doc['dataset_ids'].append(ds._id)

                    if 'dataset' in doc:
                        del doc['dataset']

                    self.collection.save(doc)
                except Exception, e:
                    print e

    def allmigration08__add_train_records_count(self):
        self.target = {'train_records_count': {'$exists': False}}
        self.update = {'$set': {'train_records_count': 0}}

    # def allmigration09__clear_importhandler(self):
    #     for doc in self.collection.find():
    #         if not doc['train_import_handler'] is None:
    #             print doc['train_import_handler'].id
    #             handler = app.db.ImportHandler.find_one({'_id': doc['train_import_handler'].id})
    #             if handler is None:
    #                 doc['train_import_handler'] = None
    #                 self.collection.save(doc)
    #         if not doc['test_import_handler'] is None:
    #             print doc['test_import_handler'].id
    #             handler = app.db.ImportHandler.find_one({'_id': doc['test_import_handler'].id})
    #             if handler is None:
    #                 doc['test_import_handler'] = None
    #                 self.collection.save(doc)

    def allmigration10__add_current_task_id(self):
        self.target = {'current_task_id': {'$exists': False}}
        self.update = {'$set': {'current_task_id': ''}}

    def allmigration11__add_features_set(self):
        self.target = {'features_set': {'$exists': False}}
        self.update = {'$set': {'features_set': None}}

    def allmigration11__add_features_set_id(self):
        self.target = {'features_set_id': {'$exists': False}}
        self.update = {'$set': {'features_set_id': None}}

    def allmigration12_add_classifier(self):
        self.target = {'classifier': {'$exists': False}}
        self.update = {'$set': {'classifier': None}}

    def allmigration13__fill_features(self):
         model_list = app.db.Model.find()
         for model in model_list:
            if not model['features']:
                continue

            features_set = app.db.FeatureSet.from_model_features_dict(model.name, model.features)
            classifier = app.db.Classifier.from_model_features_dict(model.name, model.features)
            model.features_set_id = str(features_set._id)
            model.features_set = features_set
            model.classifier = classifier
            model.save()


class TestMigration(DbMigration):  # pragma: no cover
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

    def allmigration03__add_created_by(self):
        self.target = {'created_by': {'$exists': False}}
        self.update = {'$set': {'created_by': {}}}

    def allmigration04__add_current_task_id(self):
        self.target = {'current_task_id': {'$exists': False}}
        self.update = {'$set': {'current_task_id': ''}}

    def allmigration05__add_examples_placement(self):
        self.target = {'examples_placement': {'$exists': False}}
        self.update = {'$set': {'examples_placement': 'Amazon S3'}}

    def allmigration06__add_examples_fields(self):
        self.target = {'examples_fields': {'$exists': False}}
        self.update = {'$set': {'examples_fields': []}}


class DataSetMigration(DbMigration):  # pragma: no cover
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

    # def allmigration03__fill_data_fields(self):
    #     self.target = {
    #         'data_fields': {'$size': 0}
    #     }
    #     if not self.status:
    #         for doc in self.collection.find(self.target):
    #             dataset = app.db.DataSet.find_one({'_id': doc['_id']})
    #             row = None
    #             try:
    #                 with dataset.get_data_stream() as fp:
    #                     row = next(fp)
    #                 if row:
    #                     dataset.data_fields = json.loads(row).keys()
    #                     dataset.save()
    #             except Exception, e:
    #                 print e

    def allmigration04__add_created_by(self):
        self.target = {'created_by': {'$exists': False}}
        self.update = {'$set': {'created_by': {}}}

    def allmigration05__add_updated_by(self):
        self.target = {'updated_by': {'$exists': False}}
        self.update = {'$set': {'updated_by': {}}}

    def allmigration06__add_on_s3(self):
        self.target = {'on_s3': {'$exists': False}}
        self.update = {'$set': {'on_s3': False}}

    def allmigration07__add_current_task_id(self):
        self.target = {'current_task_id': {'$exists': False}}
        self.update = {'$set': {'current_task_id': ''}}


class InstanceMigration(DbMigration):  # pragma: no cover
    DOC_CLASS = models.Instance

    def allmigration01__add_created_by(self):
        self.target = {'created_by': {'$exists': False}}
        self.update = {'$set': {'created_by': {}}}

    def allmigration02__add_updated_by(self):
        self.target = {'updated_by': {'$exists': False}}
        self.update = {'$set': {'updated_by': {}}}


class ImportHandlerMigration(DbMigration):  # pragma: no cover
    DOC_CLASS = models.ImportHandler

    def allmigration01__add_created_by(self):
        self.target = {'created_by': {'$exists': False}}
        self.update = {'$set': {'created_by': {}}}

    def allmigration02__add_updated_by(self):
        self.target = {'updated_by': {'$exists': False}}
        self.update = {'$set': {'updated_by': {}}}


class TestExampleMigration(DbMigration):  # pragma: no cover
    DOC_CLASS = models.TestExample

    def allmigration01__add_on_s3(self):
        self.target = {'on_s3': {'$exists': False}}
        self.update = {'$set': {'on_s3': False}}
