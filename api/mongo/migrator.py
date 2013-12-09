""" Migrate to postgresql  """
import logging
import uuid
import json

from api.models import *
from api import app


class Migrator(object):
    SOURCE = None  # MongoDB doc
    DESTINATION = None
    FIELDS_TO_EXCLUDE = ['_id']
    RAISE_EXC = False
    INNER = []

    def migrate(self, parent=None, source_parent=None):
        self.IDS_MAP = {}
        NAME = self.__class__.__name__.replace('Migrator', '')
        if parent:
            print "\n ------ Migrate %s (parent = %s) -----" % \
                (NAME, parent.id)
        else:
            print "\n\n\n ===== Migrate %s =====" % NAME
        source_list = self.query_mongo_docs(parent, source_parent)
        print "Found %s objects" % source_list.count()

        for i, source_obj in enumerate(source_list):
            obj = self.DESTINATION()
            self.fill_model(obj, source_obj)
            if parent is not None:
                self.process_parent(obj, parent, source_parent)
            self.fill_extra(obj, source_obj)
            print i + 1,
            try:
                obj.save()
                self.IDS_MAP[str(source_obj._id)] = obj.id
                print "New %s added" % NAME
                self.process_inner_migrators(obj, source_obj)
            except Exception, exc:
                print "Exc. occures while saving %s" % exc
                if self.RAISE_EXC:
                    self.print_exc(source_obj, obj, exc)
                    raise
                #print "source %s" % source_obj
                app.sql_db.session.rollback()

    def query_mongo_docs(self, parent=None, source_parent=None):
        return self.SOURCE.find()

    def get_source_fields(self):
        fields = self.SOURCE.structure.keys()
        return filter(lambda a: not a in self.FIELDS_TO_EXCLUDE, fields)

    def print_exc(self, source_obj, obj, exc):
        pass

    def fill_model(self, obj, source_obj):
        source_fields = self.get_source_fields()
        for field in source_fields:
            val = source_obj[field]
            mthd_name = "clean_%s" % field
            if hasattr(self, mthd_name):
                mthd = getattr(self, mthd_name)
                val = mthd(val)
            #print field, val
            setattr(obj, field, val)

    def fill_extra(self, obj, source_obj):
        pass

    def process_inner_migrators(self, obj, source_parent):
        for migrator in self.INNER:
            migrator.migrate(parent=obj, source_parent=source_parent)
        if self.INNER:
            print "\n\n"

    def process_parent(self, obj, parent, source_parent):
        pass


# Helpers

class UniqueNameMixin(object):
    def clean_name(self, val):
        count = self.DESTINATION.query.filter_by(name=val).count()
        if count > 0:
            val += str(uuid.uuid1())
        return val


class UserInfoMixin(object):
    def clean_created_by(self, val):
        return self._clean_user(val)

    def clean_updated_by(self, val):
        return self._clean_user(val)

    def clean_trained_by(self, val):
        return self._clean_user(val)

    def _clean_user(self, val):
        if not val:
            return

        try:
            user = User.query.filter_by(uid=val['uid'])[0]
            return user.id  # .one()
        except:
            logging.error('User not found: %s', val['uid'])
            return None


# Models migrators

class UserMigrator(Migrator):
    SOURCE = app.db.User
    DESTINATION = User

user = UserMigrator()


class InstanceMigrator(Migrator, UniqueNameMixin, UserInfoMixin):
    SOURCE = app.db.Instance
    DESTINATION = Instance

instance = InstanceMigrator()


class ClassifierMigrator(Migrator, UniqueNameMixin, UserInfoMixin):
    SOURCE = app.db.Classifier
    DESTINATION = PredefinedClassifier

classifier = ClassifierMigrator()


class NamedFeatureTypeMigrator(Migrator, UserInfoMixin):
    SOURCE = app.db.NamedFeatureType
    DESTINATION = NamedFeatureType

named_type = NamedFeatureTypeMigrator()


class TransformerMigrator(Migrator, UniqueNameMixin, UserInfoMixin):
    SOURCE = app.db.Transformer
    DESTINATION = PredefinedTransformer

transformer = TransformerMigrator()


class ScalerMigrator(Migrator, UniqueNameMixin, UserInfoMixin):
    SOURCE = app.db.Scaler
    DESTINATION = PredefinedScaler

scaler = ScalerMigrator()


class FeatureMigrator(Migrator, UserInfoMixin):
    SOURCE = app.db.Feature
    DESTINATION = Feature

    def process_parent(self, obj, parent, source_parent):
        obj.feature_set = parent

    def query_mongo_docs(self, parent=None, source_parent=None):
        query = self.SOURCE.find(dict(features_set_id=str(source_parent._id)))
        return query

feature = FeatureMigrator()


class FeatureSetMigrator(Migrator, UniqueNameMixin, UserInfoMixin):
    FIELDS_TO_EXCLUDE = ['_id', 'name', 'features_dict']
    SOURCE = app.db.FeatureSet
    DESTINATION = FeatureSet
    INNER = [feature]

feature_set = FeatureSetMigrator()


class DataSetMigrator(Migrator, UserInfoMixin):
    SOURCE = app.db.DataSet
    DESTINATION = DataSet

    def process_parent(self, obj, parent, source_obj):
        obj.import_handler = parent

    def query_mongo_docs(self, parent=None, source_parent=None):
        return self.SOURCE.find(
            dict(import_handler_id=str(source_parent._id)))

ds = DataSetMigrator()


class ImportHandlerMigrator(Migrator, UserInfoMixin, UniqueNameMixin):
    SOURCE = app.db.ImportHandler
    DESTINATION = ImportHandler
    INNER = [ds]

handler = ImportHandlerMigrator()


### TODO: there is id field!!!!
class TagMigrator(Migrator, UserInfoMixin):
    SOURCE = app.db.Tag
    DESTINATION = Tag

tag = TagMigrator()


class TestMigrator(Migrator, UserInfoMixin):
    SOURCE = app.db.Test
    DESTINATION = TestResult
    FIELDS_TO_EXCLUDE = ["_id", "model", ]

    def process_parent(self, obj, parent, source_obj):
        obj.model = parent

    def clean_dataset(self, val):
        if val:
            ds_id = ds.IDS_MAP.get(str(val["_id"]), None)
            if ds_id:
                return DataSet.query.get(ds_id)

    def fill_extra(self, obj, source_obj):
        obj.memory_usage = source_obj.memory_usage.get('training', None)

test = TestMigrator()


class WeightMigrator(Migrator):
    SOURCE = app.db.Weight
    DESTINATION = Weight
    FIELDS_TO_EXCLUDE = ["model_id", '_id']
    RAISE_EXC = True

    def process_parent(self, obj, parent, source_obj):
        obj.model = parent

weights = WeightMigrator()


class WeightsCategoryMigrator(Migrator):
    SOURCE = app.db.WeightsCategory
    DESTINATION = WeightsCategory
    FIELDS_TO_EXCLUDE = ["model_id", '_id']
    RAISE_EXC = True

    def process_parent(self, obj, parent, source_obj):
        obj.model = parent

weights_category = WeightsCategoryMigrator()


class ModelMigrator(Migrator, UserInfoMixin, UniqueNameMixin):
    SOURCE = app.db.Model
    DESTINATION = Model
    RAISE_EXC = True
    FIELDS_TO_EXCLUDE = ['_id', 'features']
    INNER = [test, weights_category, weights]

    def print_exc(self, source_obj, obj, exc):
        print obj.name

    # TODO: Tags!
    def fill_extra(self, obj, source_obj):
        obj.classifier = \
            {'type': source_obj.classifier['type'],
             'params': source_obj.classifier['params']}
        obj.memory_usage = source_obj.memory_usage.get('training', None)
        # Looking for feature set
        set_id = feature_set.IDS_MAP[source_obj.features_set_id]
        obj.features_set = FeatureSet.query.get(set_id)

        # # Looking for import handlers
        _id = handler.IDS_MAP[str(source_obj.test_import_handler._id)]
        obj.test_import_handler = ImportHandler.query.get(_id)
        _id = handler.IDS_MAP[str(source_obj.train_import_handler._id)]
        obj.train_import_handler = ImportHandler.query.get(_id)

model = ModelMigrator()


#MIGRATOR_PROCESS = [user, handler, feature_set, model]
MIGRATOR_PROCESS = [user, instance, named_type, classifier,
                    transformer, scaler, handler,
                    feature_set, model]


def migrate():
    from sqlalchemy import create_engine
    app.sql_db.drop_all()

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    app.sql_db.metadata.create_all(engine)
    app.sql_db.create_all()

    print "Start migration to postgresql"
    for migrator in MIGRATOR_PROCESS:
        migrator.migrate()
