from collections import defaultdict

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, deferred, backref
from sqlalchemy.sql import expression

from api.base.models import db, BaseModel, JSONType, S3File
from api.logs.models import LogMessage
from api.ml_models.models import Model
from api.import_handlers.models import DataSet


class TestResult(db.Model, BaseModel):
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

    __tablename__ = 'test_result'

    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum(*STATUSES, name='test_statuses'))
    error = db.Column(db.String(300))

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(Model, backref=backref('tests',
                                                cascade='all,delete'))
    model_name = db.Column(db.String(200))

    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id',
                                                     ondelete='SET NULL'))
    dataset = relationship(DataSet, foreign_keys=[data_set_id])

    examples_count = db.Column(db.Integer)
    examples_fields = db.Column(postgresql.ARRAY(db.String))
    examples_size = db.Column(db.Float)

    parameters = db.Column(JSONType)
    classes_set = db.Column(postgresql.ARRAY(db.String))
    accuracy = db.Column(db.Float)
    metrics = db.Column(JSONType)
    memory_usage = db.Column(db.Integer)

    vect_data = deferred(db.Column(S3File))

    def get_vect_data(self, num):
        from pickle import loads
        data = loads(self.vect_data)
        return data.getrow(num).todense().tolist()[0]

    def set_error(self, error, commit=True):
        self.error = str(error)[:299]
        self.status = TestResult.STATUS_ERROR
        if commit:
            self.save()

    @property
    def exports(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.model_tests.tasks.get_csv_results',
        )

    @property
    def confusion_matrix_calculations(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.model_tests.tasks.calculate_confusion_matrix',
        )


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

    test_result_id = db.Column(db.Integer, db.ForeignKey('test_result.id'))
    test_result = relationship('TestResult', backref=backref('examples',
                                                cascade='all,delete'))
    test_name = db.Column(db.String(200))

    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship('Model')
    model_name = db.Column(db.String(200))

    @property
    def is_weights_calculated(self):
        return self.weighted_data_input and self.weighted_data_input != {}

    def calc_weighted_data(self):
        if not self.data_input:
            return None

        from api.ml_models.helpers.features import get_features_vect_data
        model = self.model
        feature_model = model.get_trainer()._feature_model
        data = get_features_vect_data(self.test_result.get_vect_data(self.num),
                                      feature_model.features.items(),
                                      feature_model.target_variable)

        from api.ml_models.helpers.weights import get_example_params
        model_weights = list(model.weights)
        weighted_data = dict(get_example_params(
            model_weights, self.data_input, data))
        self.weighted_data_input = weighted_data
        self.save()

    @classmethod
    def get_grouped(cls, field, model_id, test_result_id):
        cursor = cls.query.filter_by(
            model_id=model_id, test_result_id=test_result_id
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
    def get_data(cls, test_result_id, fields):
        db_fields = []
        for field in fields:
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

        cursor = cls.query.filter_by(
            test_result_id=test_result_id).with_entities(*db_fields)

        for row in cursor.all():
            yield dict(zip(row.keys(), row))
