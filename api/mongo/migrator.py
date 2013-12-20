""" Migrate to postgresql  """
import logging
import uuid
from sqlalchemy.engine import reflection
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData, Table, DropTable, \
    ForeignKeyConstraint, DropConstraint

from api.models import *
from api import app
from api.mongo.models import Model as OldModel

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])


class Migrator(object):
    SOURCE = None  # MongoDB doc
    DESTINATION = None
    FIELDS_TO_EXCLUDE = ['_id']
    RAISE_EXC = False
    INNER = []
    IDS_MAP = {}

    def migrate_one(self, source_obj):
        print "migrate one for"
        parent = None
        i = 0
        obj = self.DESTINATION()
        NAME = self.__class__.__name__.replace('Migrator', '')
        try:
                self.fill_model(obj, source_obj)
                if parent is not None:
                    self.process_parent(obj, parent, source_parent)
                self.fill_extra(obj, source_obj)
                print i + 1,
                obj.save()
                self.IDS_MAP[str(source_obj._id)] = obj.id
                print "New %s added" % NAME
                self.process_inner_migrators(obj, source_obj)
        except Exception, exc:
            print exc
            app.sql_db.session.rollback()
            raise
        return obj

    def migrate(self, parent=None, source_parent=None):
#        self.IDS_MAP = {}
        NAME = self.__class__.__name__.replace('Migrator', '')
        if parent:
            print "\n ------ Migrate %s (parent = %s) -----" % \
                (NAME, parent.id)
        else:
            print "\n\n\n ===== Migrate %s =====" % NAME
        source_list = self.query_mongo_docs(parent, source_parent)
        print "Found %s objects" % source_list.count()

        for i in xrange(0, source_list.count()):
            source_obj = source_list[i]
            obj = self.DESTINATION()
            try:
                self.fill_model(obj, source_obj)
                if parent is not None:
                        self.process_parent(obj, parent, source_parent)
                self.fill_extra(obj, source_obj)
                print i + 1, "saving", obj, source_obj._id, obj.id

                self.save_obj(obj)
                self.IDS_MAP[str(source_obj._id)] = obj.id
                print "added %s" % NAME
                self.process_inner_migrators(obj, source_obj)
            except:
                raise

    def save_obj(self, obj):
        obj.save()

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
            val = source_obj.get(field, None)
            if val is None:
                continue
            mthd_name = "clean_%s" % field
            if hasattr(self, mthd_name):
                mthd = getattr(self, mthd_name)
                val = mthd(val)
#            print field, val
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
            user = User.query.filter_by(uid=val['uid']).one()
            return user
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

    def fill_extra(self, obj, source_obj):
        tr = obj.transformer
        if tr:
            tr_type = tr['type']
            tr_dict = {'type': tr_type, 'params': {}}
            from api.features.config import TRANSFORMERS
            params_list = TRANSFORMERS[tr_type]['parameters']
            for param in params_list:
                val = obj.transformer.get(param, None)
                if val is not None:
                    tr_dict['params'][param] = val
            obj.transformer = tr_dict

    def process_parent(self, obj, parent, source_parent):
        obj.feature_set = parent

    def query_mongo_docs(self, parent=None, source_parent=None):
        query = self.SOURCE.find(dict(features_set_id=str(source_parent._id)))
        return query

    def save_obj(self, obj):
        from sqlalchemy.exc import IntegrityError
        try:
            obj.save()
        except IntegrityError, exc:
            print "\n\nERROR", exc
            app.sql_db.session.rollback()


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

    def fill_extra(self, obj, source_obj):
        obj.name = obj.name[:200]
        obj.error = obj.error[:300]

ds = DataSetMigrator()


class ImportHandlerMigrator(Migrator, UserInfoMixin, UniqueNameMixin):
    SOURCE = app.db.ImportHandler
    DESTINATION = ImportHandler
    INNER = [ds]
    FIELDS_TO_EXCLUDE = ['_id', 'data', 'type']

    def fill_extra(self, obj, source_obj):
        obj.data = replace(source_obj['data'])

    def query_mongo_docs(self, parent=None, source_parent=None):
        query = self.SOURCE.find({'type': 'sql'})
        return query


REPLACES = {
    'process-as': 'process_as',
    'target-features': 'target_features',
    'to-csv': 'to_csv',
    'value-path': 'value_path',
    'target-schema': 'target_schema',
    'key-path': 'key_path'
}


def replace(data, replace_dict=REPLACES):
    data_str = json.dumps(data)

    for key, val in replace_dict.iteritems():
        data_str = data_str.replace(key, val)
    return json.loads(data_str)


handler = ImportHandlerMigrator()


### TODO: there is id field!!!!
class TagMigrator(Migrator, UserInfoMixin):
    FIELDS_TO_EXCLUDE = ['_id', 'id']
    SOURCE = app.db.Tag
    DESTINATION = Tag

tag = TagMigrator()


class TestMigrator(Migrator, UserInfoMixin):
    SOURCE = app.db.Test
    DESTINATION = TestResult
    FIELDS_TO_EXCLUDE = ["_id", "model", "exports",
                         "confusion_matrix_calculations"]

    def process_parent(self, obj, parent, source_obj):
        obj.model = parent

    def clean_dataset(self, val):
        if val:
            ds_id = ds.IDS_MAP.get(str(val._DBRef__id), None)
            if ds_id:
                return DataSet.query.get(ds_id)

    def query_mongo_docs(self, parent=None, source_parent=None):
        query = self.SOURCE.find({'model_id': str(source_parent._id)})
        return query

    def fill_extra(self, obj, source_obj):
        memory_usage = source_obj.get('memory_usage', None)
        if memory_usage:
            obj.memory_usage = memory_usage.get('testing', None)
        else:
            obj.memory_usage = None

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
    FIELDS_TO_EXCLUDE = ['_id', 'features', 'tags', 'features_set',
                         'features_set_id', 'trainer',
                         'test_import_handler', 'train_import_handler']
    INNER = [test]

    def print_exc(self, source_obj, obj, exc):
        print obj.name

    def fill_extra(self, obj, source_obj):
        print "Filling extra data in model", \
            source_obj._id, obj.name, source_obj.updated_on
        if source_obj.classifier:
            obj.classifier = {'type': source_obj.classifier['type'],
                              'params': source_obj.classifier['params']}
        else:
            obj.classifier = None

        #source_obj.save()
        source_obj = app.db.Model.find_one({'_id': source_obj._id})
        trainer = source_obj.get_trainer()
        #if trainer is None and source_obj.fs:
        #    trainer = source_obj.fs.trainer

        if trainer:
            obj.set_trainer(trainer)
        else:
            if source_obj.status == 'Trained':
                #import pdb; pdb.set_trace()
                raise Exception("Trained model should contains trainer field!")

        obj.memory_usage = source_obj.memory_usage.get('training', None)
        if source_obj.tags:
            print "Searching for model tags", source_obj.tags
            tags_list = Tag.query.filter(Tag.text.in_(source_obj.tags)).all()
            print "found", tags_list
            obj.tags = tags_list

        # Looking for feature set
        _id = source_obj.features_set_id
        fset = None
        if _id is not None:
            from bson import ObjectId
            mongo_fset = app.db.FeatureSet.find_one({'_id': ObjectId(_id)})
            if mongo_fset:
                fset = feature_set.migrate_one(mongo_fset)
            print "feature set found \n\n\n", fset

        if fset is None:
            print "no features set found! \n\n"
            fset = FeatureSet()
            fset.save()

        obj.features_set = fset

        # Looking for import handlers
        if source_obj.test_import_handler:
            print source_obj.test_import_handler
            s_id = str(source_obj.test_import_handler._id)#_DBRef__id)
            _id = handler.IDS_MAP.get(s_id, None)
        if _id:
            obj.test_import_handler = ImportHandler.query.get(_id)

        if source_obj.train_import_handler:
            s_id = str(source_obj.train_import_handler._id)
            _id = handler.IDS_MAP.get(s_id, None)
        if _id:
            obj.train_import_handler = ImportHandler.query.get(_id)
        obj.save()

model = ModelMigrator()


MIGRATOR_PROCESS = [user, instance, named_type, classifier, tag,
                    transformer, scaler, handler,
                    model]


def migrate():
    drop_all()

    app.sql_db.metadata.create_all(engine)
    app.sql_db.create_all()

    print "Start migration to postgresql"
    for migrator in MIGRATOR_PROCESS:
        migrator.migrate()


def drop_all():
    conn = engine.connect()

    # the transaction only applies if the DB supports
    # transactional DDL, i.e. Postgresql, MS SQL Server
    trans = conn.begin()

    inspector = reflection.Inspector.from_engine(engine)

    # gather all data first before dropping anything.
    # some DBs lock after things have been dropped in
    # a transaction.

    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(
                ForeignKeyConstraint((), (), name=fk['name']))
        t = Table(table_name, metadata, *fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        conn.execute(DropConstraint(fkc))

    for table in tbs:
        conn.execute(DropTable(table))

    trans.commit()
