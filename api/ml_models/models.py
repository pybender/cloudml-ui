# Models, Tags and Weights goes here
import json

from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects import postgresql

from api.base.models import db, BaseModel
from api.db import JSONType, GridfsFile
from api.models import LogMessage


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

    name = db.Column(db.String(200))
    status = db.Column(db.Enum(*STATUSES, name='model_statuses'))
    trained_by = db.Column(JSONType)
    error = db.Column(db.String(300))

    comparable = db.Column(db.Boolean)
    weights_synchronized = db.Column(db.Boolean)

    labels = db.Column(postgresql.ARRAY(db.String))
    example_label = db.Column(db.String(100))
    example_id = db.Column(db.String(100))

    spot_instance_request_id = db.Column(db.String(100))
    memory_usage = db.Column(db.Integer)
    train_records_count = db.Column(db.Integer)
    current_task_id = db.Column(db.String(100))
    training_time = db.Column(db.Integer)

    tags = relationship('Tag', secondary=lambda: tags_table, backref='models')

    target_variable = db.Column(db.Unicode)
    feature_count = db.Column(db.Integer)

    features_set_id = db.Column(db.Integer, db.ForeignKey('feature_set.id'))
    features_set = relationship('FeatureSet')

    test_import_handler_id = db.Column(db.ForeignKey('import_handler.id'))
    test_import_handler = relationship('ImportHandler',
                                       foreign_keys=[test_import_handler_id])

    train_import_handler_id = db.Column(db.ForeignKey('import_handler.id'))
    train_import_handler = relationship('ImportHandler',
                                        foreign_keys=[train_import_handler_id])

    datasets = relationship('DataSet',
                            secondary=lambda: datasets_table)

    classifier = deferred(db.Column(JSONType))

    trainer = deferred(db.Column(GridfsFile))

    def get_trainer(self, loaded=True):
        if loaded:
            from core.trainer.store import TrainerStorage
            return TrainerStorage.loads(self.trainer.read())
        return self.trainer.read()

    @property
    def dataset(self):
        return self.datasets[0]

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
        self.trainer = Binary(TrainerStorage(trainer).dumps())
        self.target_variable = trainer._feature_model.target_variable
        self.feature_count = len(trainer._feature_model.features.keys())
        if self.status == self.STATUS_TRAINED:
            self.labels = map(str, trainer._classifier.classes_.tolist())

    def get_features_json(self):
        return json.dumps({
            'classifier': {}
        })
        # TODO
        # from api.features.models import PredefinedClassifier
        # data = self.features_set.to_dict() if self.features_set else {}
        # data['classifier'] = PredefinedClassifier.from_dict(
        #     self.classifier if self.classifier else {}).to_dict()
        # return json.dumps(data)


tags_table = db.Table(
    'model_tag', db.Model.metadata,
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

datasets_table = db.Table(
    'model_dataset', db.Model.metadata,
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id'))
)


class Tag(db.Model, BaseModel):
    """
    Model tag.
    """
    text = db.Column(db.String(200))
    count = db.Column(db.Integer)


class WeightsCategory(db.Model, BaseModel):
    """
    Represents Model Parameter Weights Category.

    NOTE: used for constructing trees of weights.
    """
    __tablename__ = 'weights_category'

    name = db.Column(db.String(200))
    short_name = db.Column(db.String(200))
    model_name = db.Column(db.String(200))

    model = db.Column(db.ForeignKey('model.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('weights_category.id'))
    parent = relationship('WeightsCategory')


class Weight(db.Model, BaseModel):
    """
    Represents Model Parameter Weight
    """
    name = db.Column(db.String(200))
    short_name = db.Column(db.String(200))
    model_name = db.Column(db.String(200))
    value = db.Column(db.Float)
    is_positive = db.Column(db.Boolean)
    css_class = db.Column(db.String)

    model_id = db.Column(db.ForeignKey('model.id'))
    model = relationship('WeightsCategory')

    parent_id = db.Column(db.Integer, db.ForeignKey('weights_category.id'))
    parent = relationship('WeightsCategory')
