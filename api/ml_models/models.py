# Models, Tags and Weights goes here

from sqlalchemy import (Integer, String, Float, Column, Boolean,
                        Enum, ForeignKey, Unicode)
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects import postgresql

from api.base.models import db, BaseModel
from api.db import JSONType, GridfsFile
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

    name = Column(String(200))
    status = Column(Enum(*STATUSES, name='model_statuses'))
    trained_by = Column(JSONType)
    error = Column(String(300))

    comparable = Column(Boolean)
    weights_synchronized = Column(Boolean)

    labels = Column(postgresql.ARRAY(String))
    example_label = Column(String(100))
    example_id = Column(String(100))

    # TODO: It's unused?
    # import_params = Column(JSONType)

    spot_instance_request_id = Column(String(100))
    memory_usage = Column(Integer)
    train_records_count = Column(Integer)
    current_task_id = Column(String(100))
    training_time = Column(Integer)

    tags = relationship('Tag', secondary=lambda: tags_table, backref='models')

    target_variable = Column(Unicode)
    feature_count = Column(Integer)

    # TODO:
    # features_set_id = Column(Integer, ForeignKey('feature_set.id'))
    # features_set = relationship('FeatureSet')

    # TODO:
    # features = relationship('Feature')

    # TODO:
    # test_import_handler_id = Column(ForeignKey('import_handler.id'))
    # train_import_handler_id = Column(ForeignKey('import_handler.id'))

    # TODO:
    # datasets = relationship('Dataset',
    #                         secondary=lambda: datasets_table, backref='models')

    # TODO:
    classifier = Column(JSONType)

    trainer = deferred(db.Column(GridfsFile))

    def get_trainer(self, loaded=True):
        if loaded:
            from core.trainer.store import TrainerStorage
            return TrainerStorage.loads(self.trainer.read())
        return self.trainer.read()

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
        #feature_type = trainer._feature_model.
        #features[self.target_variable]['type']
        if self.status == self.STATUS_TRAINED:
            self.labels = map(str, trainer._classifier.classes_.tolist())


tags_table = db.Table(
    'model_tag', db.Model.metadata,
    Column('model_id', Integer, ForeignKey('model.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)


class Tag(db.Model, BaseModel):
    """
    Model tag.
    """
    text = Column(String(200))
    count = Column(Integer)


class WeightsCategory(db.Model, BaseModel):
    """
    Represents Model Parameter Weights Category.

    NOTE: used for constructing trees of weights.
    """
    __tablename__ = 'weights_category'

    name = Column(String(200))
    short_name = Column(String(200))
    model_name = Column(String(200))

    model = Column(ForeignKey('model.id'))
    parent_id = Column(Integer, ForeignKey('weights_category.id'))
    parent = relationship('WeightsCategory')


class Weight(db.Model, BaseModel):
    """
    Represents Model Parameter Weight
    """
    name = Column(String(200))
    short_name = Column(String(200))
    model_name = Column(String(200))
    value = Column(Float)
    is_positive = Column(Boolean)
    css_class = Column(String)

    model_id = Column(ForeignKey('model.id'))
    model = relationship('WeightsCategory')

    parent_id = Column(Integer, ForeignKey('weights_category.id'))
    parent = relationship('WeightsCategory')
