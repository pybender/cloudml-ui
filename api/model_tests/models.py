"""
TestResult and TestExample models.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from collections import defaultdict
import math
import scipy

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, deferred, backref
from sqlalchemy.sql import expression

from api.base.models import db, BaseModel, JSONType, S3File
from api.logs.models import LogMessage
from api.ml_models.models import Model, Segment, Weight
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

    TEST_STATUSES = [STATUS_QUEUED, STATUS_IMPORTING, STATUS_IMPORTED,
                     STATUS_IN_PROGRESS, STATUS_STORING]

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
    roc_auc = db.Column(JSONType)
    metrics = db.Column(JSONType)
    memory_usage = db.Column(db.Integer)

    vect_data = deferred(db.Column(S3File))
    fill_weights = db.Column(db.Boolean, default=False)

    def get_vect_data(self, num, segment):
        from pickle import loads
        data = loads(self.vect_data)
        offset = 0
        for k, v in data.items():
            offset += v.shape[0]
            if k == segment:
                break
        import numpy
        if isinstance(data[segment], numpy.ndarray):
            return data[num - offset]
        return data[segment].getrow(num - offset).todense().tolist()[0]

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
    def db_exports(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.model_tests.tasks.export_results_to_db',
        )

    @property
    def confusion_matrix_calculations(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.model_tests.tasks.calculate_confusion_matrix',
            statuses=AsyncTask.STATUSES
        )

    @property
    def can_edit(self):
        if not self.model.can_edit:
            self.reason_msg = self.model.reason_msg
            return False
        return super(TestResult, self).can_edit

    @property
    def can_delete(self):
        if not self.model.can_delete:
            self.reason_msg = self.model.reason_msg
            return False
        return super(TestResult, self).can_delete

    def delete(self):
        ds = self.dataset
        super(TestResult, self).delete()
        ds.unlock()

    @property
    def test_in_progress(self):
        return self.status in self.TEST_STATUSES


class TestExample(db.Model, BaseModel):
    __tablename__ = 'test_example'

    NONAME = 'noname'
    NOT_FILED_ID = '-1'

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
    def parameters_weights(self):
        res = []

        def sort_by_weight(val):
            return -val['weight']

        def go_tree(params, prefix=''):
            for name, val in params.iteritems():
                if 'weight' in val and val['weight'] != 0:
                    if prefix:
                        val['name'] = '{0}->{1}'.format(prefix, name)
                    else:
                        val['name'] = name
                    res.append(val)
                if 'weights' in val:
                    go_tree(val['weights'], prefix=name)
            return res

        go_tree(self.weighted_data_input)

        res.sort(key=sort_by_weight)
        return res

    @property
    def is_weights_calculated(self):
        return self.weighted_data_input and self.weighted_data_input != {}

    def calc_weighted_data(self):
        if not self.data_input:
            return None

        from api.ml_models.helpers.features import get_features_vect_data
        model = self.model
        feature_model = model.get_trainer()._feature_model
        segment = 'default'
        if len(model.get_trainer().with_segmentation) > 0:
            ndata = dict([(key.replace('->', '.'), val)
                          for key, val in self.data_input.iteritems()])
            data = model.get_trainer()._apply_feature_types(ndata)
            segment = "_".join(
                [str(data[feature_name]) for feature_name in
                 model.get_trainer()._feature_model.group_by])
            features = model.get_trainer().features[segment]
            for feature_name in model.get_trainer()._feature_model.group_by:
                features.pop(feature_name)
        else:
            try:
                features = model.get_trainer().features[segment]
            except:
                features = feature_model.features

        ndata = dict([(key.replace('->', '.'), val)
                      for key, val in self.data_input.iteritems()])
        trainer = model.get_trainer()
        trainer._prepare_data(
            iter([ndata, ]), callback=None, save_raw=False, is_predict=True)
        vect_data1 = trainer._get_vectorized_data(
            segment, trainer._test_prepare_feature)

        vect = scipy.sparse.hstack(vect_data1)
        vect_data = vect.todense().tolist()[0]

        data = get_features_vect_data(vect_data,
                                      features.items(),
                                      feature_model.target_variable)

        from api.ml_models.helpers.weights import get_example_params
        segment = Segment.query.filter(
            Segment.name == segment, Segment.model == model)[0]
        model_weights = Weight.query.with_entities(
            Weight.name, Weight.value).filter(Weight.segment_id == segment.id)
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
