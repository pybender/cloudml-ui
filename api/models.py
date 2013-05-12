import json
from datetime import datetime
import cPickle as pickle

from bson import Binary
from flask.ext.mongokit import Document

from api import connection, app


@connection.register
class WeightsCategory(Document):
    """
    Represents Model Parameter Weights Category.

    NOTE: used for constructing trees of weights.
    """
    __collection__ = 'weights_categories'
    structure = {
        'name': basestring,
        'short_name': basestring,
        'model_name': basestring,

        'parent': basestring,
        'has_weights': bool,
    }


@connection.register
class Weight(Document):
    """
    Represents Model Parameter Weight
    """
    __collection__ = 'weights'
    structure = {
        'name': basestring,
        'short_name': basestring,
        'model_name': basestring,
        'value': float,
        'is_positive': bool,
        'css_class': basestring,
        'parent': basestring,
    }

app.db.Weight.collection.ensure_index(
    [
        ('name', 'text'),
        ('value', 'text')
    ],
    weights={
        'name': 10,
        'value': 5,
    }
)


@connection.register
class Model(Document):
    """
    Represents Model details and it's Tests.
    """
    STATUS_NEW = 'New'
    STATUS_QUEUED = 'Queued'
    STATUS_TRAINING = 'Training'
    STATUS_TRAINED = 'Trained'
    STATUS_ERROR = 'Error'

    __collection__ = 'models'
    structure = {
        'name': basestring,
        'status': basestring,
        'created_on': datetime,
        'updated_on': datetime,
        'error': basestring,

        'features': dict,
        'target_variable': unicode,

        # Import data to train and test options
        'import_params': list,
        'importhandler': dict,
        'train_importhandler': dict,

        'trainer': None,
        'comparable': bool,

        'labels': list,
    }
    gridfs = {'files': ['trainer']}
    required_fields = ['name', 'created_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'status': STATUS_NEW,
                      'comparable': False, }
    use_dot_notation = True

    def get_import_handler(self, parameters=None, is_test=False):
        from core.importhandler.importhandler import ExtractionPlan, \
            ImportHandler
        handler = json.dumps(self.importhandler if is_test
                             else self.train_importhandler)
        plan = ExtractionPlan(handler, is_file=False)
        handler = ImportHandler(plan, parameters)
        return handler

    def run_test(self, parameters=True, callback=None):
        if self.trainer:
            trainer = pickle.loads(self.trainer)
        else:
            trainer = pickle.loads(self.fs.trainer)
        test_handler = self.get_import_handler(parameters, is_test=True)
        metrics = trainer.test(test_handler, callback=callback)
        raw_data = trainer._raw_data
        trainer.clear_temp_data()
        return metrics, raw_data

    def set_trainer(self, trainer):
        self.fs.trainer = Binary(pickle.dumps(trainer))
        self.target_variable = trainer._feature_model.target_variable
        #feature_type = trainer._feature_model.
        #features[self.target_variable]['type']
        if self.status == self.STATUS_TRAINED:
            self.labels = map(str, trainer._classifier.classes_.tolist())

    def set_weights(self, positive, negative):
        from helpers.weights import calc_weights_css
        positive_weights = calc_weights_css(positive, 'green')
        negative_weights = calc_weights_css(negative, 'red')
        weight_list = positive_weights + negative_weights
        weight_list.sort(key=lambda a: abs(a['weight']))
        weight_list.reverse()

        # Adding weights and weights categories to db
        category_names = []
        for weight in weight_list:
            name = weight['name']
            splitted_name = name.split('->')
            long_name = ''
            count = len(splitted_name)
            for i, sname in enumerate(splitted_name):
                parent = long_name
                long_name = '%s.%s' % (long_name, sname) \
                            if long_name else sname
                params = {'model_name': self.name,
                          'parent': parent,
                          'short_name': sname}
                if i == (count - 1):
                    params.update({'name': weight['name'],
                                   'value': weight['weight'],
                                   'is_positive': bool(weight['weight'] > 0),
                                   'css_class': weight['css_class']})
                    app.db.Weight.collection.insert(params)
                else:
                    if sname not in category_names:
                        # Adding a category, if it has not already added
                        category_names.append(sname)
                        params.update({'name': long_name})
                        app.db.WeightsCategory.collection.insert(params)

    def delete(self):
        params = {'model_name': self.name}
        app.db.TestExample.collection.remove(params)
        app.db.Test.collection.remove(params)
        self.collection.remove({'_id': self._id})


@connection.register
class Test(Document):
    STATUS_QUEUED = 'Queued'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_COMPLETED = 'Completed'
    STATUS_ERROR = 'Error'

    __collection__ = 'tests'
    structure = {
        'name': basestring,
        'model_name': basestring,
        'status': basestring,
        'error': basestring,
        'created_on': datetime,
        'updated_on': datetime,
        'data': dict,
        'examples_count': int,
        'parameters': dict,
        'classes_set': list,
        'accuracy': float,
        'metrics': dict,
        'model': Model,
        # Raw test data
        #'examples': [TestExample ],
    }
    required_fields = ['name', 'created_on', 'updated_on',
                       'status']
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'status': STATUS_QUEUED}
    use_dot_notation = True
    use_autorefs = True

    @classmethod
    def generate_name(cls, model, base_name='Test'):
        count = model.tests.count()
        return "%s-%s" % (base_name, count + 1)

    @property
    def data_count(self):
        return self.data.count()

    def delete(self):
        params = dict(test_name=self.name,
                      model_name=self.model_name)
        app.db.TestExample.collection.remove(params)
        self.collection.remove({'_id': self._id})


@connection.register
class TestExample(Document):
    __collection__ = 'example'

    structure = {
        'created_on': datetime,
        'data_input': dict,
        'weighted_data_input': dict,

        'name': basestring,
        'label': basestring,
        'pred_label': basestring,
        'prob': list,
        'test': Test,

        'test_name': basestring,
        'model_name': basestring,
    }
    use_autorefs = True
    default_values = {'created_on': datetime.utcnow}
    required_fields = ['created_on', ]


@connection.register
class ImportHandler(Document):
    TYPE_DB = 'Db'
    TYPE_REQUEST = 'Request'
    __collection__ = 'handlers'
    structure = {
        'name': basestring,
        'type': basestring,
        'created_on': datetime,
        'updated_on': datetime,
        'data': dict,
    }
    required_fields = ['name', 'created_on', 'updated_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'type': TYPE_DB}
    use_dot_notation = True

    def __repr__(self):
        return '<Import Handler %r>' % self.name
