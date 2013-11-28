from collections import defaultdict
from bson import ObjectId

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.sql import expression

from api import app
from api.base.models import db, BaseModel
from api.logs.models import LogMessage
from api.db import JSONType, GridfsFile


class Test(db.Model, BaseModel):
    LOG_TYPE = LogMessage.RUN_TEST

    STATUS_QUEUED = 'Queued'
    STATUS_IMPORTING = 'Importing'
    STATUS_IMPORTED = 'Imported'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_STORING = 'Storing'
    STATUS_COMPLETED = 'Completed'
    STATUS_ERROR = 'Error'

    STATUSES = [STATUS_QUEUED, STATUS_IMPORTING, STATUS_IMPORTED,
                STATUS_IN_PROGRESS, STATUS_STORING, STATUS_COMPLETED,
                STATUS_ERROR]

    name = db.Column(db.String(200))
    status = db.Column(db.Enum(*STATUSES, name='test_statuses'))
    error = db.Column(db.String(300))

    model_id = db.Column(db.String(200))
    model_name = db.Column(db.String(200))

    dataset_id = db.Column(db.String(200))

    examples_count = db.Column(db.Integer)
    examples_fields = db.Column(postgresql.ARRAY(db.String))
    examples_size = db.Column(db.Float)

    parameters = db.Column(JSONType)
    classes_set = db.Column(postgresql.ARRAY(db.String))
    accuracy = db.Column(db.Float)
    metrics = db.Column(JSONType)
    memory_usage = db.Column(db.Integer)
    current_task_id = db.Column(db.String(100))

    vect_data = deferred(db.Column(GridfsFile))

    def get_vect_data(self, num):
        from pickle import loads
        data = loads(self.vect_data.read())
        return data.getrow(num).todense().tolist()[0]

    @property
    def model(self):
        return app.db.Model.get_from_id(ObjectId(self.model_id))

    @property
    def dataset(self):
        return app.db.DataSet.get_from_id(ObjectId(self.dataset_id))


class TestExample(db.Model, BaseModel):
    __tablename__ = 'test_example'

    example_id = db.Column(db.String(100))
    name = db.Column(db.String(100))
    label = db.Column(db.String(100))
    pred_label = db.Column(db.String(100))
    num = db.Column(db.Integer)

    prob = db.Column(postgresql.ARRAY(db.Float))

    data_input = db.Column(JSONType)
    weighted_data_input = db.Column(JSONType)

    test_id = db.Column(db.Integer, db.ForeignKey('test.id'))
    test = relationship('Test', backref='examples')
    test_name = db.Column(db.String(200))

    model_id = db.Column(db.String(200))
    model_name = db.Column(db.String(200))

    @property
    def is_weights_calculated(self):
        return self.weighted_data_input and self.weighted_data_input != {}

    def calc_weighted_data(self):
        if not self.data_input:
            return None

        from api.helpers.features import get_features_vect_data
        model = app.db.Model.find_one({'_id': ObjectId(self.model_id)})
        feature_model = model.get_trainer()._feature_model
        data = get_features_vect_data(self.test.get_vect_data(self.num),
                                      feature_model.features.items(),
                                      feature_model.target_variable)

        from api.helpers.weights import get_example_params
        model_weights = app.db.Weight.find({'model_id': self.model_id})
        weighted_data = dict(get_example_params(
            model_weights, self.data_input, data))
        self.weighted_data_input = weighted_data
        self.save()

    @classmethod
    def get_grouped(cls, field, model_id, test_id):
        cursor = cls.query.filter_by(
            model_id=model_id, test_id=test_id
        ).with_entities(
            cls.pred_label,
            cls.label,
            cls.prob,
            # Selecting field from json object isn't supported by alchemy,
            # using literal column instead
            expression.literal_column("data_input->>'{!s}'".format(
                field)).label('group')
        )

        groups = defaultdict(list)
        for row in cursor.all():
            groups[row[3]].append({
                'label': row[0],
                'pred': row[1],
                'prob': row[2],
            })

        return [{
            field: key,
            'list': value
        } for key, value in groups.iteritems()]

    @classmethod
    def get_data(cls, test_id, fields):
        db_fields = []
        for field in fields:
            if field == '_id':
                field = 'id'
            if field == 'id':
                field = 'example_id'
            db_field = getattr(cls, field, None)
            if db_field:
                db_fields.append(db_field)
            else:
                # Selecting field from json object isn't supported by alchemy,
                # using literal column instead
                db_fields.append(
                    expression.literal_column("data_input->>'{!s}'".format(
                        field.replace('data_input.', ''))).label(field)
                )

        cursor = cls.query.filter_by(test_id=test_id).with_entities(
            *db_fields
        )

        for row in cursor.all():
            yield dict(zip(row.keys(), row))
