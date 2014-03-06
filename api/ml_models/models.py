# Models, Tags and Weights goes here
import json
from functools import partial

from sqlalchemy.orm import relationship, deferred, backref
from sqlalchemy.dialects import postgresql
from sqlalchemy import Index, func
from sqlalchemy.ext.declarative import declared_attr

from api.base.models import db, BaseModel, BaseMixin, JSONType, S3File
from api.logs.models import LogMessage


class Model(db.Model, BaseModel):
    """
    Represents Model details.
    """
    LOG_TYPE = LogMessage.TRAIN_MODEL

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

    STATUSES = [STATUS_NEW, STATUS_QUEUED, STATUS_IMPORTING, STATUS_IMPORTED,
                STATUS_REQUESTING_INSTANCE, STATUS_INSTANCE_STARTED,
                STATUS_TRAINING, STATUS_TRAINED, STATUS_ERROR, STATUS_CANCELED]

    name = db.Column(db.String(200), nullable=False, unique=True)
    status = db.Column(db.Enum(*STATUSES, name='model_statuses'),
                       default=STATUS_NEW)
    trained_by_id = db.Column(db.ForeignKey('user.id', ondelete='SET NULL'))

    trained_by = relationship("User", foreign_keys='Model.trained_by_id')

    error = db.Column(db.String(300))

    comparable = db.Column(db.Boolean)
    weights_synchronized = db.Column(db.Boolean)

    labels = db.Column(postgresql.ARRAY(db.String), default=[])
    example_label = db.Column(db.String(100))
    example_id = db.Column(db.String(100))

    spot_instance_request_id = db.Column(db.String(100))
    memory_usage = db.Column(db.Integer)
    train_records_count = db.Column(db.Integer)
    training_time = db.Column(db.Integer)

    tags = relationship('Tag', secondary=lambda: tags_table, backref='models')

    target_variable = db.Column(db.Unicode)
    feature_count = db.Column(db.Integer)

    features_set_id = db.Column(db.Integer, db.ForeignKey('feature_set.id'))
    features_set = relationship('FeatureSet', uselist=False)

    test_import_handler_id = db.Column(db.ForeignKey('import_handler.id',
                                                     ondelete='SET NULL'))
    test_import_handler = relationship('ImportHandler',
                                       foreign_keys=[test_import_handler_id])

    train_import_handler_id = db.Column(db.ForeignKey('import_handler.id',
                                                      ondelete='SET NULL'))
    train_import_handler = relationship('ImportHandler',
                                        foreign_keys=[train_import_handler_id])

    datasets = relationship('DataSet',
                            secondary=lambda: data_sets_table)

    classifier = deferred(db.Column(JSONType))

    trainer = deferred(db.Column(S3File))
    trainer_size = db.Column(db.Integer, default=0)

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

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def get_trainer(self, loaded=True):
        if loaded:
            from core.trainer.store import TrainerStorage
            return TrainerStorage.loads(self.trainer)
        return self.trainer

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
        return handler.get_fields() if handler else []

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
        return metrics, raw_data

    def set_trainer(self, trainer):
        from bson import Binary
        from core.trainer.store import TrainerStorage
        trainer_data = Binary(TrainerStorage(trainer).dumps())
        self.trainer = trainer_data
        self.trainer_size = len(trainer_data)
        self.target_variable = trainer._feature_model.target_variable
        self.feature_count = len(trainer._feature_model.features.keys())
        if self.status == self.STATUS_TRAINED:
            self.labels = map(str, trainer._classifier.classes_.tolist())

    def get_features_json(self):
        data = self.features_set.features
        if data is None:
            self.features_set.modified = True
            data = self.features_set.features
        data['classifier'] = self.classifier
        return json.dumps(data)

    @property
    def features(self):
        return self.get_features_json()

    def delete_metadata(self, delete_log=True):
        from api.base.models import db
        if delete_log:
            LogMessage.delete_related_logs(self.id)

        def _del(items):
            for item in items:
                db.session.delete(item)

        _del(self.tests)
        _del(self.weight_categories)
        _del(self.weights)
        db.session.commit()

        self.comparable = False
        self.save()


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


class Tag(db.Model, BaseMixin):
    """
    Model tag.
    """
    text = db.Column(db.String(200))
    count = db.Column(db.Integer)


class WeightsCategory(db.Model, BaseMixin):
    """
    Represents Model Parameter Weights Category.

    NOTE: used for constructing trees of weights.
    """
    __tablename__ = 'weights_category'

    name = db.Column(db.String(200))
    short_name = db.Column(db.String(200))
    model_name = db.Column(db.String(200))

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('weight_categories'))

    parent = db.Column(db.String(200))


def _setup_search(table_name, fields, event, schema_item, bind):
    bind.execute('alter table {0} add column fts tsvector'.format(table_name))
    bind.execute('create index {0}_fts_index on {0} using gin(fts)'.format(
        table_name))

    fields_str = ', '.join(fields)
    bind.execute("""create trigger {0}_search_update
        before update or insert on {0} for each row execute procedure
        tsvector_update_trigger(fts, 'pg_catalog.english', {1})""".format(
        table_name, fields_str))


class Weight(db.Model, BaseMixin):
    """
    Represents Model Parameter Weight
    """
    name = db.Column(db.String(200))
    short_name = db.Column(db.String(200))
    model_name = db.Column(db.String(200))
    value = db.Column(db.Float)
    is_positive = db.Column(db.Boolean)
    css_class = db.Column(db.String)

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('weights'))

    parent = db.Column(db.String(200))

Weight.__table__.append_ddl_listener(
    'after-create', partial(_setup_search, Weight.__table__.name,
                            ['name']))
