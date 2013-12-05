from datetime import datetime

from flask.ext.mongokit import Document as BaseDocument
from api import app


@app.conn.register
class WeightsCategory(BaseDocument):
    """
    Represents Model Parameter Weights Category.

    NOTE: used for constructing trees of weights.
    """
    __collection__ = 'weights_categories'
    structure = {
        'name': basestring,
        'short_name': basestring,
        'model_id': basestring,
        'model_name': basestring,

        'parent': basestring,
    }


@app.conn.register
class Weight(BaseDocument):
    """
    Represents Model Parameter Weight
    """
    __collection__ = 'weights'
    structure = {
        'name': basestring,
        'short_name': basestring,
        'model_id': basestring,
        'model_name': basestring,
        'value': float,
        'is_positive': bool,
        'css_class': basestring,
        'parent': basestring,
    }
    use_dot_notation = True

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


@app.conn.register
class ImportHandler(BaseDocument):
    TYPE_DB = 'Db'
    TYPE_REQUEST = 'Request'

    __collection__ = 'handlers'

    structure = {
        'name': basestring,
        'type': basestring,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
        'data': dict,
        'import_params': list,
    }
    required_fields = ['name', 'created_on', 'updated_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'type': TYPE_DB,
                      'created_by': {},
                      'updated_by': {},
                      }
    use_dot_notation = True


@app.conn.register
class DataSet(BaseDocument):
    __collection__ = 'dataset'
    LOG_TYPE = 'importdata_log'

    STATUS_IMPORTING = 'Importing'
    STATUS_UPLOADING = 'Uploading'
    STATUS_IMPORTED = 'Imported'
    STATUS_ERROR = 'Error'

    FORMAT_JSON = 'json'
    FORMAT_CSV = 'csv'
    FORMATS = [FORMAT_JSON, FORMAT_CSV]

    structure = {
        'name': basestring,
        'status': basestring,
        'error': basestring,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
        'data': basestring,
        'import_params': dict,
        'import_handler_id': basestring,
        'on_s3': bool,
        'compress': bool,
        'filename': basestring,
        'filesize': long,
        'records_count': int,
        'time': int,
        'data_fields': list,
        'current_task_id': basestring,
        'format': basestring,
    }
    required_fields = ['name', 'created_on', 'updated_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'error': '',
                      'on_s3': False,
                      'compress': True,
                      'status': STATUS_IMPORTING,
                      'data_fields': [],
                      'created_by': {},
                      'updated_by': {},
                      'format': FORMAT_JSON, }
    use_dot_notation = True


@app.conn.register
class Tag(BaseDocument):
    __collection__ = 'tags'
    structure = {
        'id': basestring,
        'text': basestring,
        # Count of models with this tag
        'count': int,
    }
    default_values = {'count': 1}
    use_dot_notation = True


@app.conn.register
class FeatureSet(BaseDocument):
    """
    Represents list of the features with schema name.
    """
    __collection__ = 'features_sets'

    FIELDS_TO_SERIALIZE = ('schema_name', )

    structure = {
        'name': basestring,
        'schema_name': basestring,
        'features_count': int,
        'target_variable': basestring,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
        # features dictionary (without classifier) to use in cloudml core
        'features_dict': dict,
    }
    required_fields = ['created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'features_count': 0,
        'features_dict': {'schema-name': '',
                          'features': [],
                          "feature-types": []}
    }
    use_dot_notation = True
    use_autorefs = True


from core.trainer.classifier_settings import CLASSIFIERS


@app.conn.register
class Classifier(BaseDocument):
    __collection__ = 'classifier'

    TYPES_LIST = CLASSIFIERS.keys()
    NO_PARAMS_KEY = True
    FIELDS_TO_SERIALIZE = ('type', 'params')

    structure = {
        'name': basestring,
        'type': basestring,
        'params': dict,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict
    }
    required_fields = ['created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
    }
    use_dot_notation = True

app.db.Classifier.collection.ensure_index('name', unique=True)


@app.conn.register
class Model(BaseDocument):
    """
    Represents Model details and it's Tests.
    """
    LOG_TYPE = 'trainmodel_log'

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

    __collection__ = 'models'
    structure = {
        'name': basestring,
        'status': basestring,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
        'trained_by': dict,
        'error': basestring,

        'classifier': dict,
        'features': dict,
        'features_set': FeatureSet,
        'features_set_id': basestring,
        'feature_count': int,
        'target_variable': unicode,

        # Import data to train and test options
        'import_params': list,

        'test_import_handler': ImportHandler,
        'train_import_handler': ImportHandler,
        # ids of datasets used for model training
        'dataset_ids': list,

        'train_importhandler': dict,
        'importhandler': dict,

        'trainer': None,
        'comparable': bool,
        'weights_synchronized': bool,

        'labels': list,
        # Fieldname of the example title from raw data
        'example_label': basestring,
        'example_id': basestring,
        'tags': list,

        'spot_instance_request_id': basestring,
        'memory_usage': dict,
        'train_records_count': int,
        'current_task_id': basestring,
        'training_time': int
    }
    gridfs = {'files': ['trainer']}
    required_fields = ['name', 'created_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'status': STATUS_NEW,
                      'comparable': False,
                      'tags': [],
                      'weights_synchronized': False,
                      'spot_instance_request_id': '',
                      'memory_usage': {},
                      'created_by': {},
                      'updated_by': {},
                      'trained_by': {},
                      'dataset_ids': [],
                      }
    use_dot_notation = True
    use_autorefs = True


@app.conn.register
class Test(BaseDocument):
    LOG_TYPE = 'runtest_log'

    STATUS_QUEUED = 'Queued'
    STATUS_IMPORTING = 'Importing'
    STATUS_IMPORTED = 'Imported'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_STORING = 'Storing'
    STATUS_COMPLETED = 'Completed'
    STATUS_ERROR = 'Error'

    EXPORT_STATUS_IN_PROGRESS = 'In Progress'
    EXPORT_STATUS_COMPLETED = 'Completed'

    MATRIX_STATUS_IN_PROGRESS = 'In Progress'
    MATRIX_STATUS_COMPLETED = 'Completed'

    EXAMPLES_TO_AMAZON_S3 = 'Amazon S3'
    EXAMPLES_DONT_SAVE = 'Do not save'
    EXAMPLES_MONGODB = 'Mongo DB'
    EXAMPLES_STORAGE_CHOICES = (EXAMPLES_TO_AMAZON_S3,
                                EXAMPLES_DONT_SAVE,
                                EXAMPLES_MONGODB)

    __collection__ = 'tests'
    structure = {
        'name': basestring,
        'model_name': basestring,
        'model_id': basestring,
        'status': basestring,
        'error': basestring,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'data': dict,

        'examples_count': int,
        'examples_placement': basestring,
        'examples_fields': list,
        'examples_size': float,

        'parameters': dict,
        'classes_set': list,
        'accuracy': float,
        'metrics': dict,
        'model': Model,
        # dataset which used for running test
        'dataset': DataSet,
        # Raw test data
        #'examples': [TestExample ],
        'memory_usage': dict,
        'exports': list,
        'current_task_id': basestring,
        'confusion_matrix_calculations': list,
    }
    required_fields = ['name', 'created_on', 'updated_on',
                       'status']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'status': STATUS_QUEUED,
        'memory_usage': {},
        'exports': [],
        'created_by': {},
        'examples_size': 0.0,
        'confusion_matrix_calculations': [],
    }
    use_dot_notation = True
    use_autorefs = True


@app.conn.register
class TestExample(BaseDocument):
    __collection__ = 'example'
    S3_KEY = 'text_example_'

    structure = {
        'created_on': datetime,
        'updated_on': datetime,
        'data_input': dict,
        'weighted_data_input': dict,

        'id': basestring,
        'name': basestring,

        'label': basestring,
        'pred_label': basestring,
        'prob': list,
        'vect_data': list,
        'test': Test,

        'test_name': basestring,
        'model_name': basestring,
        'test_id': basestring,
        'model_id': basestring,

        'on_s3': bool,
    }
    use_autorefs = True
    default_values = {'created_on': datetime.utcnow, 'on_s3': False}
    required_fields = ['created_on', ]
    use_dot_notation = True


@app.conn.register
class Instance(BaseDocument):
    __collection__ = 'instances'
    structure = {
        'name': basestring,
        'description': basestring,
        'ip': basestring,
        'type': basestring,
        'is_default': bool,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
    }
    required_fields = ['name', 'created_on', 'updated_on', 'ip', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'is_default': False,
                      'created_by': {},
                      'updated_by': {}}
    use_dot_notation = True

    def __repr__(self):
        return '<Instance %r>' % self.name


@app.conn.register
class User(BaseDocument):
    __collection__ = 'users'
    structure = {
        'uid': basestring,
        'name': basestring,
        'odesk_url': basestring,
        'email': basestring,
        'portrait_32_img': basestring,
        'created_on': datetime,
        'updated_on': datetime,
        'auth_token': basestring,
    }
    required_fields = ['uid', 'name', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
    }
    use_dot_notation = True

    def __repr__(self):
        return '<User %r>' % self.name


# Features specific models

@app.conn.register
class NamedFeatureType(BaseDocument):
    __collection__ = 'named_feature_types'

    TYPES_LIST = ['boolean', 'int', 'float', 'numeric', 'date',
                  'map', 'categorical_label', 'categorical',
                  'text', 'regex', 'composite']
    FIELDS_TO_SERIALIZE = ('name', 'type', 'input_format', 'params')

    structure = {
        'name': basestring,
        'type': basestring,
        'input_format': basestring,
        'params': dict,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
    }
    required_fields = ['name', 'type', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
    }
    use_dot_notation = True

    def __repr__(self):
        return '<Named Feature Type %r>' % self.name

app.db.NamedFeatureType.collection.ensure_index('name', unique=True)


# TODO: move and use it in cloudml project
TRANSFORMERS = {
    'Dictionary': {
        #'mthd': get_dict_vectorizer,
        'parameters': ['separator', 'sparse'],
        'default': {},  # default value
        'defaults': {}  # default values of the parameters
    },
    'Count': {
        #'mthd': get_count_vectorizer,
        'parameters': ['charset', 'charset_error',
                       'strip_accents', 'lowercase',
                       'stop_words', 'token_pattern',
                       'analyzer', 'max_df', 'min_df',
                       'max_features', 'vocabulary',
                       'binary'],
        'default': '',
        'defaults': {}
    },
    'Tfidf': {
        #'mthd': get_tfidf_vectorizer,
        'parameters': ['charset', 'charset_error',
                       'strip_accents', 'lowercase',
                       'analyzer', 'stop_words',
                       'token_pattern', 'max_df',
                       'min_df', 'max_features',
                       'vocabulary', 'binary',
                       'use_idf', 'smooth_idf',
                       'sublinear_tf'],
        'default': '',
        'defaults': {}
    },
    'Lda': {
        #'mthd': get_count_vectorizer,
        'parameters': ['charset', 'charset_error',
                        'strip_accents', 'lowercase',
                        'stop_words', 'token_pattern',
                        'analyzer', 'max_df', 'min_df',
                        'max_features', 'vocabulary',
                        'binary',
                        'num_topics','id2word', 'alpha',
                        'eta', 'distributed', 'topic_file'],
        'default': '',
        'defaults': {}
    },
    'Lsi': {
        #'mthd': get_count_vectorizer,
        'parameters': ['charset', 'charset_error',
                        'strip_accents', 'lowercase',
                        'stop_words', 'token_pattern',
                        'analyzer', 'max_df', 'min_df',
                        'max_features', 'vocabulary',
                        'binary',
                        'num_topics','id2word',
                        'distributed', 'onepass',
                        'power_iters', 'extra_samples',
                        'topic_file'],
        'default': '',
        'defaults': {}
    }
}


@app.conn.register
class Transformer(BaseDocument):
    __collection__ = 'transformers'

    TYPES_LIST = TRANSFORMERS.keys()
    NO_PARAMS_KEY = True
    FIELDS_TO_SERIALIZE = ('name', 'type', 'params')

    structure = {
        'name': basestring,
        'type': basestring,
        'params': dict,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
    }
    required_fields = ['type', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
    }
    use_dot_notation = True

    def __repr__(self):
        return '<Transformer %r>' % self.type

app.db.Transformer.collection.ensure_index('name', unique=True)


#from core.trainer.scalers import SCALERS
from core.trainer.scalers import MinMaxScaler, StandardScaler
SCALERS = {
    'MinMaxScaler': {
        'class': MinMaxScaler,
        'defaults': {
            'feature_range_min': 0,
            'feature_range_max': 1,
            'copy': True},
        'parameters': ['feature_range_min', 'feature_range_max', 'copy']},
    'StandardScaler': {
        'class': StandardScaler,
        'defaults': {
            'copy': True,
            'with_std': True,
            'with_mean': True},
        'parameters': ['copy', 'with_std', 'with_mean']
    }
}


@app.conn.register
class Scaler(BaseDocument):
    __collection__ = 'scalers'

    TYPES_LIST = SCALERS.keys()
    NO_PARAMS_KEY = True
    FIELDS_TO_SERIALIZE = ('name', 'type', 'params')

    structure = {
        'name': basestring,
        'type': basestring,
        'params': dict,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
    }
    required_fields = ['type', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
    }
    use_dot_notation = True

    def __repr__(self):
        return '<Scaler %r>' % self.type

app.db.Transformer.collection.ensure_index('name', unique=True)


@app.conn.register
class Feature(BaseDocument):
    __collection__ = 'features'

    FIELDS_TO_SERIALIZE = ('name', 'type', 'input_format', 'params',
                           'default', 'is_target_variable', 'required',
                           'transformer', 'scaler')

    structure = {
        'name': basestring,
        'type': basestring,
        #'features_set': FeatureSet,
        'features_set_id': basestring,
        'input_format': basestring,
        'params': dict,
        'required': bool,
        'scaler': dict,
        'transformer': dict,
        'default': None,
        'is_target_variable': bool,

        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
    }
    required_fields = ['name', 'type', 'created_on',
                       'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'required': True,
        'is_target_variable': False,
        'params': {},
    }
    use_dot_notation = True
    use_autorefs = True

app.db.Feature.collection.ensure_index('feature_set_id')
