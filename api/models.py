import json
import StringIO
import logging
from boto.exception import S3ResponseError
import os
from bson import ObjectId
from datetime import datetime
from os.path import join, exists
from os import makedirs

from bson import Binary
from flask.ext.mongokit import Document
from flask import request, has_request_context

from core.trainer.streamutils import streamingiterload

from api import app, celery
from api.amazon_utils import AmazonS3Helper


FIELDS_MAP = {'input_format': 'input-format',
              'is_target_variable': 'is-target-variable',
              'required': 'is-required',
              'schema_name': 'schema-name'}

class BaseDocument(Document):
    NO_PARAMS_KEY = False

    def _set_user(self, user):
        if user:
            field = 'created_by' if '_id' not in self else 'updated_by'
            if field in self:
                self[field] = {
                    '_id': user._id,
                    'uid': user.uid,
                    'name': user.name
                }

    def save(self, *args, **kwargs):
        if has_request_context():
            self._set_user(getattr(request, 'user', None))
        return super(BaseDocument, self).save(*args, **kwargs)

    def terminate_task(self):
        if hasattr(self, 'current_task_id'):
            try:
                celery.control.revoke(self.current_task_id, terminate=True)
            except Exception as e:
                logging.exception(e)

    @classmethod
    def from_dict(cls, Doc, obj_dict, extra_fields={},
                  filter_params=None, save=True, add_new=False):
        obj_dict.update(extra_fields)
        fields_list = list(cls.FIELDS_TO_SERIALIZE) + extra_fields.keys()

        if add_new:
            obj = None 
        else:
            if filter_params is None:
                filter_params = {'name': obj_dict['name']}
            obj = Doc.find_one(filter_params)

        if not obj:
            obj = Doc()
            for field in fields_list:
                dict_field_name = FIELDS_MAP.get(field, field)
                if cls.NO_PARAMS_KEY and field == 'params':
                    params_fields = set(obj_dict.keys()) - set(cls.FIELDS_TO_SERIALIZE)
                    value = dict([(name, obj_dict[name]) for name in params_fields])
                else:
                    value = obj_dict.get(dict_field_name, None)
                if value is not None:
                    obj[field] = value
            if save:
                obj.save()

            return obj, True

        return obj, False

    def to_dict(self):
        data = {}
        for field in self.FIELDS_TO_SERIALIZE:
            val = getattr(self, field)
            if val is not None:
                data[field] = val
        return data


@app.conn.register
class LogMessage(BaseDocument):
    TRAIN_MODEL = 'trainmodel_log'
    IMPORT_DATA = 'importdata_log'
    RUN_TEST = 'runtest_log'
    CONFUSION_MATRIX_LOG = 'confusion_matrix_log'
    TYPE_CHOICES = (TRAIN_MODEL, IMPORT_DATA, RUN_TEST,
                    CONFUSION_MATRIX_LOG)

    __collection__ = 'logs'
    structure = {
        # error, warning
        'level': basestring,
        # operation type: run test, train model, etc
        'type': basestring,
        'params': dict,
        'content': basestring,
        'created_on': datetime,
    }
    default_values = {'created_on': datetime.utcnow}
    use_dot_notation = True

    @classmethod
    def delete_related_logs(cls, obj, level=None):
        # TODO: implement level
        app.db.LogMessage.collection.remove({'params.obj': str(obj._id),
                                             'type': obj.LOG_TYPE})


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
                      'updated_by': {}}
    use_dot_notation = True

    def create_dataset(self, params, run_import_data=True):
        #from api.utils import slugify
        dataset = app.db.DataSet()
        str_params = "-".join(["%s=%s" % item
                              for item in params.iteritems()])
        dataset.name = "%s: %s" % (self.name, str_params)
        dataset.import_handler_id = str(self._id)
        dataset.import_params = params
        # filename = '%s-%s.json' % (slugify(self.name)
        # str_params.replace('=', '_'))
        # dataset.data = filename
        dataset.save(validate=True)
        dataset.set_file_path()
        return dataset

    def delete(self):
        datasets = app.db.DataSet.find({'import_handler_id': str(self._id)})
        for ds in datasets:
            ds.delete()

        expr = {'$or': [{'test_import_handler.$id': self._id},
                        {'train_import_handler.$id': self._id}]}
        models = app.db.Model.find(expr)

        def unset(model, handler_type='train'):
            handler = getattr(model, '%s_import_handler' % handler_type)
            if handler['_id'] == self._id:
                setattr(model, '%s_import_handler' % handler_type, None)
                model.changed = True

        for model in models:
            model.changed = False
            unset(model, 'train')
            unset(model, 'test')
            if model.changed:
                model.save()

        super(ImportHandler, self).delete()

    def __repr__(self):
        return '<Import Handler %r>' % self.name


@app.conn.register
class DataSet(BaseDocument):
    __collection__ = 'dataset'
    LOG_TYPE = 'importdata_log'

    STATUS_IMPORTING = 'Importing'
    STATUS_UPLOADING = 'Uploading'
    STATUS_IMPORTED = 'Imported'
    STATUS_ERROR = 'Error'

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
                      'updated_by': {}}
    use_dot_notation = True

    def __init__(self, *args, **kwargs):
        super(DataSet, self).__init__(*args, **kwargs)

    def get_s3_download_url(self, expires_in=3600):
        helper = AmazonS3Helper()
        return helper.get_download_url(str(self._id), expires_in)

    def set_file_path(self):
        data = '%s.%s' % (self._id, 'gz' if self.compress else 'json')
        self.data = data
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        self.filename = join(path, data)
        self.save()

    @property
    def data(self):
        if not self.on_s3:
            raise Exception('Invalid oper')

        if not hasattr(self, '_data'):
            self._data = self.load_from_s3()
        return self._data

    def get_data_stream(self):
        import gzip
        #import zlib
        if not self.on_s3 or exists(self.filename):
            logging.info('Loading data from local file')
            open_meth = gzip.open if self.compress else open
            return open_meth(self.filename, 'r')
        else:
            logging.info('Loading data from Amazon S3')
            stream = StringIO.StringIO(self.data)
            if self.compress:
                logging.info('Decompress data')
                return gzip.GzipFile(fileobj=stream, mode='r')
                #data = zlib.decompress(data)
            return stream

    def load_from_s3(self):
        helper = AmazonS3Helper()
        return helper.load_key(str(self._id))

    def save_to_s3(self):
        meta = {'handler': self.import_handler_id,
                'dataset': self.name,
                'params': str(self.import_params)}
        helper = AmazonS3Helper()
        # helper.save_key(str(self._id), self.filename, meta)
        helper.save_gz_file(str(self._id), self.filename, meta)
        helper.close()
        self.on_s3 = True
        self.save()

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def delete(self):
        # Stop task
        self.terminate_task()

        # Remove from tests
        app.db.Test.collection.update({
            'dataset.$id': self._id
        }, {'$set': {'dataset': None}}, multi=True)

        # Remove from models
        app.db.Model.collection.update({
            'dataset_ids': self._id
        }, {'$pull': {'dataset_ids': self._id}}, multi=True)

        super(DataSet, self).delete()
        LogMessage.delete_related_logs(self)

        # TODO: check import handler type
        try:
            os.remove(self.filename)
        except OSError:
            pass
        if self.on_s3:
            from api.amazon_utils import AmazonS3Helper
            helper = AmazonS3Helper()
            try:
                helper.delete_key(str(self._id))
            except S3ResponseError as e:
                logging.exception(str(e))

    def save(self, *args, **kwargs):
        if self.status != self.STATUS_ERROR:
            self.error = ''
        super(DataSet, self).save(*args, **kwargs)

    def __repr__(self):
        return '<Dataset %r>' % self.name


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

    @classmethod
    def update_tags_count(cls, old_list, new_list):
        tags_to_update = list(set(old_list) ^ set(new_list))
        for text in tags_to_update:
            tag = app.db.Tag.find_one({'text': text})
            if tag is None:
                tag = app.db.Tag()
                tag.text = tag.id = text
                tag.count = 1
                tag.save()
            else:
                tag.count = app.db.Model.find({
                    'tags': text
                }).count()
                if tag.count == 0:
                    tag.delete()
                else:
                    tag.save()


@app.conn.register
class FeatureSet(BaseDocument):
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
    }
    required_fields = ['created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'features_count': 0,
    }
    use_dot_notation = True
    use_autorefs = True

    def to_dict(self):
        data = {'schema-name': self.schema_name,
                'features': [],
                "feature-types": []}

        named_types = []  # named types to include to the file
        features = app.db.Feature.find({'features_set_id': str(self._id)})
        for feature in features:
            data['features'].append(feature.to_dict())
            if feature.type not in NamedFeatureType.TYPES_LIST:
                named_types.append(feature.type)

        for name in named_types:
            named_type = app.db.NamedFeatureType.find_one({'name': name})
            data["feature-types"].append(named_type.to_dict())
        
        return data

    @classmethod
    def from_model_features_dict(cls, name, features_dict):
        if not features_dict:
            features_set = app.db.FeatureSet()
            features_set.name = name
            features_set.save()
            return features_set

        features_set, is_new = app.db.FeatureSet.from_dict(\
            app.db.FeatureSet, features_dict,
            extra_fields={'name': name,
                          'features_count': len(features_dict['features'])},
            add_new=True)

        for feature_type in features_dict['feature-types']:
            app.db.NamedFeatureType.from_dict(app.db.NamedFeatureType,
                                              feature_type)

        for feature_dict in features_dict['features']:
            f_id = str(features_set._id)

            feature, is_new = app.db.Feature.from_dict(\
                app.db.Feature, feature_dict, add_new=True,
                extra_fields={'features_set': features_set,
                              'features_set_id': f_id})

            if feature.is_target_variable:
                features_set.target_variable = feature.name
                features_set.save()

        return features_set

    def __repr__(self):
        return '<Feature Set %r>' % self.name


from core.trainer.classifier_settings import CLASSIFIERS

@app.conn.register
class Classifier(BaseDocument):
    __collection__ = 'classifier'

    TYPES_LIST = CLASSIFIERS.keys()
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
    required_fields = ['created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
    }
    use_dot_notation = True

    @classmethod
    def from_model_features_dict(cls, name, features_dict):
        if not features_dict:
            classifier = app.db.Classifier()
            classifier.name = name
            classifier.save()
            return classifier

        classifier, is_new = app.db.Classifier.from_dict(\
            app.db.Classifier, features_dict['classifier'],
            add_new=True,
            extra_fields={'name': name}
        )
        return classifier

    def __repr__(self):
        return '<Classifier %r>' % self.name


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

        'classifier': Classifier,
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

    @property
    def dataset(self):
        if self.dataset_ids:
            return app.db.DataSet.find_one({'_id': self.dataset_ids[0]})
        else:
            return None

    @property
    def datasets_list(self):
        return app.db.DataSet.find({'_id': {'$in': self.dataset_ids}})

    def get_trainer(self, loaded=True):
        trainer = self.trainer or self.fs.trainer
        if loaded:
            from core.trainer.store import TrainerStorage
            return TrainerStorage.loads(trainer)
        return trainer

    # TODO: unused code
    def get_import_handler(self, parameters=None, is_test=False):  # pragma: no cover
        from core.importhandler.importhandler import ExtractionPlan, \
            ImportHandler
        handler = json.dumps(self.importhandler if is_test
                             else self.train_importhandler)
        plan = ExtractionPlan(handler, is_file=False)
        handler = ImportHandler(plan, parameters)
        return handler

    def run_test(self, dataset, callback=None):
        trainer = self.get_trainer()
        fp = dataset.get_data_stream()
        try:
            metrics = trainer.test(
                streamingiterload(fp),
                callback=callback,
                save_raw=True)
        finally:
            fp.close()
        raw_data = trainer._raw_data
        trainer.clear_temp_data()
        return metrics, raw_data

    def set_trainer(self, trainer):
        from core.trainer.store import TrainerStorage
        self.fs.trainer = Binary(TrainerStorage(trainer).dumps())
        self.target_variable = trainer._feature_model.target_variable
        self.feature_count = len(trainer._feature_model.features.keys())
        #feature_type = trainer._feature_model.
        #features[self.target_variable]['type']
        if self.status == self.STATUS_TRAINED:
            self.labels = map(str, trainer._classifier.classes_.tolist())

    def delete(self):
        # Stop running task
        self.terminate_task()
        self.delete_metadata()
        self.collection.remove({'_id': self._id})
        app.db.Tag.update_tags_count(self.tags, [])

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def delete_metadata(self, delete_log=True):
        if delete_log:
            LogMessage.delete_related_logs(self)
        params = {'model_id': str(self._id)}
        app.db.Test.collection.remove(params)
        app.db.TestExample.collection.remove(params)
        app.db.WeightsCategory.collection.remove(params)
        app.db.Weight.collection.remove(params)
        self.comparable = False
        self.save()


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
    }
    use_dot_notation = True
    use_autorefs = True

    # TODO: unused code
    @classmethod
    def generate_name(cls, model, base_name='Test'):  # pragma: no cover
        count = model.tests.count()
        return "%s-%s" % (base_name, count + 1)

    # TODO: unused code
    @property
    def data_count(self):  # pragma: no cover
        return self.data.count()

    @property
    def temp_data_filename(self):
        if not hasattr(self, '_temp_data_filename'):
            name = 'Test_raw_data-{0!s}.dat'.format(self._id)
            path = app.config['DATA_FOLDER']

            if not exists(path):
                makedirs(path)
            self._temp_data_filename = os.path.join(path, name)

        return self._temp_data_filename

    def delete(self):
        # Stop running task
        self.terminate_task()
        params = dict(test_name=self.name,
                      model_name=self.model_name)
        app.db.TestExample.collection.remove(params)
        self.collection.remove({'_id': self._id})
        LogMessage.delete_related_logs(self)

    def get_examples_full_data(self, fields=None, data_input_params=None):
        """
        Get examples with data_input fields from dataset stored at s3
        :param fields: list of needed examples fields
        :return: iterator
        """
        example_id_field = self.model.example_id
        logging.info('Getting examples full data. Id field is %s', example_id_field)

        if fields:
            for required_field in ['_id', 'id', example_id_field]:
                if required_field not in fields:
                    fields.append(required_field)

        filter_dict = {'model_id': self.model_id, 'test_id': str(self._id)}

        examples_on_s3 = app.db.TestExample.find(
            dict(filter_dict.items() + {'on_s3': True}.items())
        ).count()
        logging.info("%s examples on Amazon S3 found", examples_on_s3)

        if not examples_on_s3:
            logging.info("Don't download dataset - no examples on S3")
            if fields:
                if data_input_params:
                    filter_dict.update(data_input_params)
                    fields += data_input_params.keys()
                else:
                    fields += ['data_input']
            for example in app.db.TestExample.find(filter_dict, fields):
                if example.get('data_input'):
                    for key, value in example['data_input'].iteritems():
                        example['data_input.{0}'.format(key)] = value
                    del example['data_input']
                yield example
            return

        examples_data = dict([(epl['id'], epl)
                              for epl in
                              app.db.TestExample.find(filter_dict, fields)])
        logging.debug('Examples count %d' % len(examples_data))
        with self.dataset.get_data_stream() as dataset_data_stream:
            logging.info('Getting dataset stream')
            for (i, row) in enumerate(dataset_data_stream):
                if i % 100 == 0:
                    logging.info('Processing %s row' % i)


                data = json.loads(row)
                example_id = str(data[example_id_field])
                example = examples_data.get(example_id)
                if i == 0:
                    logging.debug('row %s, example %s' % (row, example))
                if not example:
                    if i == 0:
                        logging.warning('Example %s did not found' % (example_id))
                    continue
                for key in data:
                    new_key = 'data_input.{0}'.format(key.replace('.', '->'))
                    example[new_key] = data[key]
                if data_input_params:
                    skip_it = False
                    for k, v in data_input_params.items():
                        if example[k] != v:
                            skip_it = True
                            break
                    if skip_it:
                        continue
                yield example


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

    @property
    def s3_key(self):
        return '{0!s}_{1!s}'.format(self.S3_KEY, self._id)

    @property
    def is_weights_calculated(self):
        return self.weighted_data_input != {}

    def calc_weighted_data(self):
        data_input = None
        if self.on_s3:
            data = self._load_from_s3()
            if data:
                data_input = json.loads(data)
        else:
            data_input = self.data_input

        if not data_input:
            return None

        from api.helpers.features import get_features_vect_data
        from bson.objectid import ObjectId
        model = app.db.Model.find_one({'_id': ObjectId(self.model_id)})
        feature_model = model.get_trainer()._feature_model
        data = get_features_vect_data(self.vect_data,
                                      feature_model.features.items(),
                                      feature_model.target_variable)

        from helpers.weights import get_example_params
        model_weights = app.db.Weight.find({'model_id': self.model_id})
        weighted_data = dict(get_example_params(model_weights, data_input, data))
        self.weighted_data_input = weighted_data
        self.save(check_keys=False)

    def _save_to_s3(self, data):
        meta = {
            'example_id': self.id,
            'test_id': self.test_id,
            'model_id': self.model_id,
        }
        helper = AmazonS3Helper()
        helper.save_key_string(self.s3_key, json.dumps(data), meta)
        helper.close()

    def _load_from_s3(self):
        helper = AmazonS3Helper()
        return helper.load_key(self.s3_key)

    def delete(self):
        helper = AmazonS3Helper()
        helper.delete_key(self.s3_key)
        super(TestExample, self).delete()


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

    @classmethod
    def get_hash(cls, token):
        import hashlib
        return hashlib.sha224(token).hexdigest()

    @classmethod
    def authenticate(cls, oauth_token, oauth_token_secret, oauth_verifier):
        from auth import OdeskAuth
        auth = OdeskAuth()
        _oauth_token, _oauth_token_secret = auth.authenticate(
            oauth_token, oauth_token_secret, oauth_verifier)
        info = auth.get_my_info(_oauth_token, _oauth_token_secret,
                                oauth_verifier)

        user = app.db.User.find_one({'uid': info['auth_user']['uid']})
        if not user:
            user = app.db.User()
            user.uid = info['auth_user']['uid']

        import uuid
        auth_token = str(uuid.uuid1())
        user.auth_token = cls.get_hash(auth_token)

        user.name = '{0} {1}'.format(
            info['auth_user']['first_name'],
            info['auth_user']['last_name'])
        user.odesk_url = info['info']['profile_url']
        user.portrait_32_img = info['info']['portrait_32_img']
        user.email = info['auth_user']['mail']

        user.save()
        return auth_token, user

    @classmethod
    def get_auth_url(cls):
        from auth import OdeskAuth
        auth = OdeskAuth()
        return auth.get_auth_url()


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
        'is_predefined': bool,
    }
    required_fields = ['type', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'is_predefined': False,
    }
    use_dot_notation = True

    def __repr__(self):
        return '<Transformer %r>' % self.name


#from core.trainer.scalers import SCALERS
from core.trainer.scalers import MinMaxScaler, StandardScaler
SCALERS = {
    'MinMaxScaler': {
        'class': MinMaxScaler,
        'defaults': {
            'feature_range_min': 0,
            'feature_range_max': 1,
            'copy': True},
        'parameters': ['feature_range_min', 'feature_range_max', 'copy']
        },
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
    FIELDS_TO_SERIALIZE = ('name', 'type', 'params')

    structure = {
        'name': basestring,
        'type': basestring,
        'params': dict,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
        'is_predefined': bool,
    }
    required_fields = ['type', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'is_predefined': False,
    }
    use_dot_notation = True

    def __repr__(self):
        return '<Scaler %r>' % self.name


@app.conn.register
class Feature(BaseDocument):
    __collection__ = 'features'

    FIELDS_TO_SERIALIZE = ('name', 'type', 'input_format', 'params',
                           'default', 'is_target_variable', 'required',
                           'transformer')

    structure = {
        'name': basestring,
        'type': basestring,
        'features_set': FeatureSet,
        'features_set_id': basestring,
        'input_format': basestring,
        'transformer': Transformer,
        'params': dict,
        'required': bool,
        'scaler': Scaler,
        'default': None,
        'is_target_variable': bool,
        'created_on': datetime,
        'created_by': dict,
        'updated_on': datetime,
        'updated_by': dict,
    }
    required_fields = ['name', 'type', 'created_on', 'updated_on']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'required': True,
        'is_target_variable': False,
        'params': {},
    }
    use_dot_notation = True
    use_autorefs = True

    def delete(self):
        _id = self.features_set_id
        super(Feature, self).delete()
        feature_set = app.db.FeatureSet.get_from_id(ObjectId(_id))
        feature_set.features_count -= 1
        feature_set.save()

    @classmethod
    def from_dict(cls, Doc, obj_dict, extra_fields={},
                  filter_params=None, save=True, add_new=True):
        if 'transformer' in obj_dict:
            obj_dict['transformer'] = app.db.Transformer.from_dict(\
                app.db.Transformer, obj_dict['transformer'],
                {'name': '%s-transformer' % obj_dict['name']})[0]
        
        if 'scaler' in obj_dict:
            obj_dict['scaler'] = app.db.Scaler.from_dict(\
                app.db.Transformer, obj_dict['scaler'],
                {'name': '%s-scaler' % obj_dict['name']})[0]
        
        feature, is_new = super(Feature, cls).from_dict(Doc, obj_dict, extra_fields,
                                                filter_params, save, add_new)
        return feature, is_new

    def to_dict(self):
        data = super(Feature, self).to_dict()
        if self.transformer:
            data['transformer'] = self.transformer.to_dict()
        print data
        return data

    def __repr__(self):
        return '<Feature %r>' % self.name
