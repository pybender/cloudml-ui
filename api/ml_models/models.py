# Models, Tags and Weights goes here
import json
import logging
from functools import partial

from sqlalchemy.orm import relationship, deferred, backref, foreign, remote
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from sqlalchemy import Index, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import event, and_

from api.base.models import db, BaseModel, BaseMixin, JSONType, S3File
from api.logs.models import LogMessage
from api.amazon_utils import AmazonS3Helper


class BaseTrainedEntity(object):
    """
    Base class for entities, that could be trained
    (models, pretrained transformers).
    """
    STATUS_NEW = 'New'
    STATUS_QUEUED = 'Queued'
    STATUS_IMPORTING = 'Importing'
    STATUS_IMPORTED = 'Imported'
    STATUS_REQUESTING_INSTANCE = 'Requesting Instance'
    STATUS_INSTANCE_STARTED = 'Instance Started'
    STATUS_TRAINING = 'Training'
    STATUS_TRAINED = 'Trained'
    STATUS_ERROR = 'Error'
    STATUS_CANCELED = 'Canceled'
    STATUS_FILLING_WEIGHTS = 'Filling Weights'

    STATUSES = [STATUS_NEW, STATUS_QUEUED, STATUS_IMPORTING, STATUS_IMPORTED,
                STATUS_REQUESTING_INSTANCE, STATUS_INSTANCE_STARTED,
                STATUS_TRAINING, STATUS_FILLING_WEIGHTS, STATUS_TRAINED,
                STATUS_ERROR, STATUS_CANCELED]

    @declared_attr
    def name(cls):
        return db.Column(db.String(200), nullable=False, unique=True)

    @declared_attr
    def status(cls):
        from api.base.utils import convert_name
        name = convert_name(cls.__name__)
        return db.Column(db.Enum(*cls.STATUSES, name='%s_statuses' % name),
                         default=cls.STATUS_NEW)

    @declared_attr
    def error(cls):
        return db.Column(db.String(300))

    @declared_attr
    def spot_instance_request_id(cls):
        return db.Column(db.String(100))

    @declared_attr
    def memory_usage(cls):
        return db.Column(db.Integer)

    @declared_attr
    def trainer(cls):
        return deferred(db.Column(S3File))

    @declared_attr
    def trainer_size(cls):
        return db.Column(db.BigInteger, default=0)

    @declared_attr
    def training_time(cls):
        return db.Column(db.Integer)

    @declared_attr
    def trained_by_id(cls):
        return db.Column(
            db.ForeignKey('user.id', ondelete='SET NULL'))

    @declared_attr
    def trained_by(cls):
        return relationship(
            "User", foreign_keys='%s.trained_by_id' % cls.__name__)

    @declared_attr
    def train_import_handler_type(cls):
        return db.Column(db.String(200), default='json')

    @declared_attr
    def train_import_handler_id(cls):
        return db.Column(db.Integer, nullable=True)

    @property
    def train_import_handler(self):
        return getattr(
            self, "rel_train_import_handler_%s" % self.train_import_handler_type)

    @train_import_handler.setter
    def train_import_handler(self, handler):
        self.train_import_handler_id = handler.id
        self.train_import_handler_type = handler.TYPE

    # Fields declaration ended

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def get_trainer(self, loaded=True, force_load=False):
        if loaded:
            if not hasattr(self, 'loaded_trainer') or force_load:
                from core.trainer.store import TrainerStorage
                self.loaded_trainer = TrainerStorage.loads(self.trainer)
            return self.loaded_trainer
        return self.trainer

    def set_trainer(self, trainer):
        from bson import Binary
        from core.trainer.store import TrainerStorage
        trainer_data = Binary(TrainerStorage(trainer).dumps())
        self.trainer = trainer_data
        self.trainer_size = len(trainer_data)

    def get_trainer_filename(self):
        # we don't use sqlalchemy to avoid auto loading of trainer file
        # intoo trainer object
        sql = text("SELECT trainer from model where id=:id")
        trainer_filename, = db.engine.execute(sql, id=self.id).first()
        return trainer_filename

    def get_trainer_s3url(self, expires_in=3600):
        trainer_filename = self.get_trainer_filename()
        if self.status != self.STATUS_TRAINED or not trainer_filename:
            return None
        helper = AmazonS3Helper()
        return helper.get_download_url(trainer_filename, expires_in)

    def train(*args, **kwargs):
        pass


class Model(db.Model, BaseModel, BaseTrainedEntity):
    """
    Represents Model details.
    """
    LOG_TYPE = LogMessage.TRAIN_MODEL

    comparable = db.Column(db.Boolean)
    weights_synchronized = db.Column(db.Boolean)

    labels = db.Column(postgresql.ARRAY(db.String), default=[])
    example_label = db.Column(db.String(100))
    example_id = db.Column(db.String(100))

    train_records_count = db.Column(db.Integer)

    tags = relationship('Tag', secondary=lambda: tags_table, backref='models')

    target_variable = db.Column(db.Unicode)
    feature_count = db.Column(db.Integer)

    features_set_id = db.Column(db.Integer, db.ForeignKey('feature_set.id'))
    features_set = relationship('FeatureSet', uselist=False, backref='model')

    test_import_handler_id = db.Column(db.Integer, nullable=True)
    test_import_handler_type = db.Column(db.String(200), default='json')

    datasets = relationship('DataSet',
                            secondary=lambda: data_sets_table)

    classifier = deferred(db.Column(JSONType))
    # Note: It could contains different keys depends to the classifier used
    visualization_data = deferred(db.Column(JSONType))

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        self.visualization_data = {}

    def visualize_model(self, data=None, status=None, commit=True, segment=None):
        def set_status(item, status):
            if not 'parameters' in item:
                item['parameters'] = {}
            item['parameters']['status'] = status

        from copy import deepcopy
        visualization_data = deepcopy(self.visualization_data or {})

        if segment is None:
            if data:
                visualization_data = data
            if status:
                set_status(visualization_data, status)
        else:
            if data is None:
                raise ValueError("data is required when segment is specified")
            else:
                # updating the visualization data of specific segment
                visualization_data[segment] = data or {}
                if status:
                    set_status(visualization_data[segment], status)

        self.visualization_data = visualization_data
        if commit:
            self.save()

    @property
    def test_import_handler(self):
        return getattr(
            self, "rel_test_import_handler_%s" % self.test_import_handler_type)

    @test_import_handler.setter
    def test_import_handler(self, handler):
        if handler is not None:
            self.test_import_handler_id = handler.id
            self.test_import_handler_type = handler.TYPE

    def create_segments(self, segments):
        for name, records in segments.iteritems():
            segment = Segment()
            segment.name = name
            segment.records = records
            segment.model = self
            segment.save()

    def __repr__(self):
        return "<Model {0}>".format(self.name)

    def save(self, commit=True):
        if self.features_set is None:
            from api.features.models import FeatureSet
            self.features_set = FeatureSet()
            db.session.add(self.features_set)
        if self.classifier is None:
            self.classifier = {}
        super(Model, self).save(commit)

    @property
    def dataset(self):
        return self.datasets[0] if len(self.datasets) else None

    @property
    def data_fields(self):
        ds = self.dataset
        return ds.data_fields if ds else []

    @property
    def test_handler_fields(self):
        handler = self.test_import_handler
        if handler:
            try:
                return handler.get_fields()
            except:
                pass
        return []

    def run_test(self, dataset, callback=None):
        trainer = self.get_trainer()
        fp = dataset.get_data_stream()
        try:
            metrics = trainer.test(
                dataset.get_iterator(fp),
                callback=callback,
                save_raw=True)
        finally:
            fp.close()
        raw_data = trainer._raw_data
        trainer.clear_temp_data()
        self.set_trainer(trainer)
        self.save()
        return metrics, raw_data

    def transform_dataset(self, dataset):
        trainer = self.get_trainer()
        fp = dataset.get_data_stream()
        try:
            return trainer.transform(dataset.get_iterator(fp))
        finally:
            fp.close()

    def set_trainer(self, trainer):
        super(Model, self).set_trainer(trainer)
        self.target_variable = trainer._feature_model.target_variable
        self.feature_count = len(trainer._feature_model.features.keys())
        if self.status == self.STATUS_TRAINED and \
                trainer.model_type == trainer.TYPE_CLASSIFICATION:
            self.labels = trainer._get_labels()

    def get_features_json(self):
        data = self.features_set.features
        if data is None:
            self.features_set.modified = True
            data = self.features_set.features
        data['features'] = [f for f in data['features']
                            if f.get('disabled', False) is False]
        data['classifier'] = self.classifier
        return json.dumps(data, indent=4)

    @property
    def features(self):
        return self.get_features_json()

    def prepare_fields_for_train(self, user, datasets=[], delete_metadata=True):
        """
        Flushes model fields while re-training.
        Removes related models, when `delete_metadata` setted.
        """
        if delete_metadata:
            from api.model_tests.models import TestResult, TestExample
            from api.base.models import db
            LogMessage.delete_related_logs(self.id)

            def _del(Cls, related_name):
                count = Cls.query.filter(Cls.model_id == self.id).delete(
                        synchronize_session=False)
                logging.info('%s %s examples to delete' % (count, related_name))

            _del(TestExample, 'test examples')
            _del(TestResult, 'tests')
            _del(Weight, 'weights')
            _del(WeightsCategory, 'weights categories')
            _del(Segment, 'segments')

        self.datasets = datasets
        self.status = self.STATUS_TRAINING
        self.visualization_data = {}
        self.error = ""
        self.trained_by = user
        self.comparable = False
        db.session.add(self)
        db.session.commit()


tags_table = db.Table(
    'model_tag', db.Model.metadata,
    db.Column('model_id', db.Integer, db.ForeignKey(
        'model.id', ondelete='CASCADE', onupdate='CASCADE')),
    db.Column('tag_id', db.Integer, db.ForeignKey(
        'tag.id', ondelete='CASCADE', onupdate='CASCADE'))
)

data_sets_table = db.Table(
    'model_dataset', db.Model.metadata,
    db.Column('model_id', db.Integer, db.ForeignKey(
        'model.id', ondelete='CASCADE', onupdate='CASCADE')),
    db.Column('data_set_id', db.Integer, db.ForeignKey(
        'data_set.id', ondelete='CASCADE', onupdate='CASCADE'))
)


transformer_data_sets_table = db.Table(
    'transformer_dataset', db.Model.metadata,
    db.Column('transformer_id', db.Integer, db.ForeignKey(
        'transformer.id', ondelete='CASCADE', onupdate='CASCADE')),
    db.Column('data_set_id', db.Integer, db.ForeignKey(
        'data_set.id', ondelete='CASCADE', onupdate='CASCADE'))
)


class Transformer(BaseModel, BaseTrainedEntity, db.Model):
    """ Represents pretrained transformer """
    from api.features.config import TRANSFORMERS
    TYPES_LIST = TRANSFORMERS.keys()
    params = db.Column(JSONType)
    field_name = db.Column(db.String(100))
    feature_type = db.Column(db.String(100))
    type = db.Column(
        db.Enum(*TYPES_LIST, name='pretrained_transformer_types'),
                nullable=False)
    datasets = relationship('DataSet',
                            secondary=lambda: transformer_data_sets_table)

    def train(self, iterator, *args, **kwargs):
        from core.transformers.transformer import Transformer
        transformer = Transformer(json.dumps(self.json), is_file=False)
        transformer.train(iterator)
        return transformer

    def set_trainer(self, transformer):
        from bson import Binary
        import cPickle as pickle
        trainer_data = Binary(pickle.dumps(transformer))
        self.trainer = trainer_data
        self.trainer_size = len(trainer_data)

    def get_trainer(self):
        import cPickle as pickle
        return pickle.loads(self.trainer)

    @property
    def json(self):
        return {
            "transformer-name": self.name,
            "field-name": self.field_name,
            "type": self.feature_type,
            "transformer": {
                "type": self.type,
                "params": self.params
            }
        }

    def load_from_json(self, json):
        self.name = json.get("transformer-name")
        self.field_name = json.get("field-name")
        self.feature_type = json.get("type")

        if "transformer" in json and json["transformer"]:
            transformer_config = json["transformer"]
            self.type = transformer_config.get("type")
            self.params = transformer_config.get("params")


def get_transformer(name):
    transformer = Transformer.query.filter(Transformer.name == name).one()
    if transformer is None:
        raise Exception('Transformer "%s" not found ' % name)
    if transformer.status != Transformer.STATUS_TRAINED:
        raise Exception('Transformer "%s" not trained' % name)
    transformer = transformer.get_trainer()
    return transformer.feature['transformer']


from api.import_handlers.models import ImportHandlerMixin

@event.listens_for(ImportHandlerMixin, "mapper_configured", propagate=True)
def setup_listener(mapper, class_):
    import_handler_type = class_.TYPE
    class_.test_import_handler = relationship(
        Model,
        primaryjoin=and_(
            class_.id == foreign(remote(Model.test_import_handler_id)),
            Model.test_import_handler_type == import_handler_type
        ),
        #cascade='all,delete',
        backref=backref(
            "rel_test_import_handler_%s" % import_handler_type,
            primaryjoin=remote(class_.id) == foreign(Model.test_import_handler_id)
        )
    )
    class_.train_import_handler = relationship(
        Model,
        primaryjoin=and_(
            class_.id == foreign(remote(Model.train_import_handler_id)),
            Model.train_import_handler_type == import_handler_type
        ),
        #cascade='all,delete',
        backref=backref(
            "rel_train_import_handler_%s" % import_handler_type,
            primaryjoin=remote(class_.id) == foreign(Model.train_import_handler_id)
        )
    )
    class_.transformers = relationship(
        Transformer,
        primaryjoin=and_(
            class_.id == foreign(remote(Transformer.train_import_handler_id)),
            Transformer.train_import_handler_type == import_handler_type
        ),
        #cascade='all,delete',
        backref=backref(
            "rel_train_import_handler_%s" % import_handler_type,
            primaryjoin=remote(class_.id) == foreign(Transformer.train_import_handler_id)
        )
    )


class Tag(db.Model, BaseMixin):
    """
    Model tag.
    """
    text = db.Column(db.String(200))
    count = db.Column(db.Integer)


class Segment(db.Model, BaseMixin):
    __tablename__ = 'segment'

    name = db.Column(db.String(200))
    records = db.Column(db.Integer)

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('segments'))


class WeightsCategory(db.Model, BaseMixin):
    """
    Represents Model Parameter Weights Category.

    NOTE: used for constructing trees of weights.
    """
    __tablename__ = 'weights_category'

    name = db.Column(db.String(200))
    short_name = db.Column(db.String(200))
    # TODO: remove it
    model_name = db.Column(db.String(200))

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('weight_categories'))

    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'))
    segment = relationship(Segment, backref=backref('weight_categories'))

    normalized_weight = db.Column(db.Float)
    class_label = db.Column(db.String(100), nullable=True)

    parent = db.Column(db.String(200))

    # TODO: Maybe have FK Weight to WeightsCategory? 
    # @aggregated('normalized_weight', sa.Column(sa.Float))
    # def normalized_weight(self):
    #     return sa.func.sum(Weight.value2)

    def __repr__(self):
        return '<Category {0}>'.format(self.name)


def _setup_search(table_name, fields, event, schema_item, bind):
    bind.execute('alter table {0} add column fts tsvector'.format(table_name))
    bind.execute('create index {0}_fts_index on {0} using gin(fts)'.format(
        table_name))

    fields_str = ', '.join(fields)
    bind.execute("""create trigger {0}_search_update
        before update or insert on {0} for each row execute procedure
        tsvector_update_trigger(fts, 'pg_catalog.english', {1})""".format(
        table_name, fields_str))

from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ColumnClause


class TestWeightColumn(ColumnClause):
    pass


@compiles(TestWeightColumn)
def compile_mycolumn(element, compiler, **kw):
    return "weight.test_weights->'%s'" % element.name


class Weight(db.Model, BaseMixin):
    """
    Represents Model Parameter Weight
    """
    name = db.Column(db.String(200))
    short_name = db.Column(db.String(200))
    model_name = db.Column(db.String(200))
    value = db.Column(db.Float)
    value2 = db.Column(db.Float)
    is_positive = db.Column(db.Boolean)
    css_class = db.Column(db.String)
    class_label = db.Column(db.String(100), nullable=True)

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('weights'))

    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'))
    segment = relationship(Segment, backref=backref('weights'))

    parent = db.Column(db.String(200))

    test_weights = db.Column(JSONType)

    @hybrid_method
    def test_weight(self, test_id):
        return TestWeightColumn(test_id)

Weight.__table__.append_ddl_listener(
    'after-create', partial(_setup_search, Weight.__table__.name,
                            ['name']))


class ClassifierGridParams(db.Model, BaseModel):
    STATUS_LIST = ('New', 'Queued', 'Calculating', 'Completed')
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('classifier_grid_params'))
    scoring = db.Column(db.String(100), default='accuracy')
    status = db.Column(
        db.Enum(*STATUS_LIST, name='classifier_grid_params_statuses'),
                nullable=False, default='New')

    train_data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id',
                                                     ondelete='SET NULL'))
    train_dataset = relationship('DataSet', foreign_keys=[train_data_set_id])

    test_data_set_id = db.Column(
        db.Integer, db.ForeignKey('data_set.id', ondelete='SET NULL'))
    test_dataset = relationship('DataSet', foreign_keys=[test_data_set_id])

    parameters = db.Column(JSONType)
    parameters_grid = db.Column(JSONType)
