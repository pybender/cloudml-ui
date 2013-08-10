import json
import StringIO
import logging
import os
from datetime import datetime
import cPickle as pickle
from os.path import join, exists
from os import makedirs

from bson import Binary
from flask.ext.mongokit import Document
from core.trainer.streamutils import streamingiterload

from api import app
from api.amazon_utils import AmazonS3Helper


@app.conn.register
class LogMessage(Document):
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
class WeightsCategory(Document):
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
class Weight(Document):
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
        'import_params': list,
    }
    required_fields = ['name', 'created_on', 'updated_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'type': TYPE_DB}
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

        expr = {'$or': [{'test_import_handler._id': self._id},
                        {'train_import_handler._id': self._id}]}
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
class DataSet(Document):
    __collection__ = 'dataset'
    LOG_TYPE = 'importdata_log'

    STATUS_IMPORTING = 'Importing'
    STATUS_IMPORTED = 'Imported'
    STATUS_ERROR = 'Error'

    structure = {
        'name': basestring,
        'status': basestring,
        'error': basestring,
        'created_on': datetime,
        'updated_on': datetime,
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
    }
    required_fields = ['name', 'created_on', 'updated_on', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'error': '',
                      'on_s3': False,
                      'compress': True,
                      'status': STATUS_IMPORTING,
                      'data_fields': []}
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
        if self.on_s3:
            logging.info('Loading data from Amazon S3')
            stream = StringIO.StringIO(self.data)
            if self.compress:
                logging.info('Decompress data')
                return gzip.GzipFile(fileobj=stream, mode='r')
                #data = zlib.decompress(data)
            return stream
        else:
            logging.info('Loading data from local file')
            open_meth = gzip.open if self.compress else open
            return open_meth(self.filename, 'r')

    def load_from_s3(self):
        helper = AmazonS3Helper()
        return helper.load_key(str(self._id))

    def save_to_s3(self):
        meta = {'handler': self.import_handler_id,
                'dataset': self.name,
                'params': str(self.import_params)}
        helper = AmazonS3Helper()
        helper.save_key(str(self._id), self.filename, meta)
        #helper.save_gz_file(str(self._id), self.filename, meta)
        helper.close()
        #logging.info("Keys in bucket: %s" % [i for i in helper.bucket.list()])
        self.on_s3 = True
        self.save()

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def delete(self):
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
            helper.delete_key(str(self._id))

    def save(self, *args, **kwargs):
        if self.status != self.STATUS_ERROR:
            self.error = ''
        super(DataSet, self).save(*args, **kwargs)

    def __repr__(self):
        return '<Dataset %r>' % self.name


@app.conn.register
class Tag(Document):
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
        def get_or_create_tag(text, increase_count=True):
            tag = app.db.Tag.find_one({'text': text})
            if tag is None:
                tag = app.db.Tag()
                tag.text = tag.id = text
                tag.count = 1
                tag.save()
            else:
                if increase_count:
                    tag.count += 1
                    tag.save()
            return tag

        for name in new_list:
            tag = get_or_create_tag(name, increase_count=not name in old_list)

        tags_to_decrease_count = set(old_list) - set(new_list)
        for text in tags_to_decrease_count:
            tag = app.db.Tag.find_one({'text': text})
            tag.count -= 1
            tag.save()


@app.conn.register
class Model(Document):
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
        'updated_on': datetime,
        'error': basestring,

        'features': dict,
        'feature_count': int,
        'target_variable': unicode,

        # Import data to train and test options
        'import_params': list,

        'test_import_handler': ImportHandler,
        'train_import_handler': ImportHandler,
        # dataset which used for model training
        'dataset': DataSet,

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
                      }
    use_dot_notation = True
    use_autorefs = True

    def get_trainer(self, loaded=True):
        trainer = self.trainer or self.fs.trainer
        if loaded:
            from core.trainer.store import TrainerStorage
            return TrainerStorage.loads(trainer)
        return trainer

    def get_import_handler(self, parameters=None, is_test=False):
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
        self.delete_metadata()
        self.collection.remove({'_id': self._id})

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


@app.conn.register
class Test(Document):
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

    __collection__ = 'tests'
    structure = {
        'name': basestring,
        'model_name': basestring,
        'model_id': basestring,
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
        # dataset which used for running test
        'dataset': DataSet,
        # Raw test data
        #'examples': [TestExample ],
        'memory_usage': dict,
        'exports': list,
    }
    required_fields = ['name', 'created_on', 'updated_on',
                       'status']
    default_values = {
        'created_on': datetime.utcnow,
        'updated_on': datetime.utcnow,
        'status': STATUS_QUEUED,
        'memory_usage': {},
        'exports': []
    }
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
        LogMessage.delete_related_logs(self)

    def get_examples_full_data(self, fields=None, data_input_params=None):
        """
        Get examples with data_input fields from dataset stored at s3
        :param fields: list of needed examples fields
        :return: iterator
        """
        example_id_field = self.model.example_id
        dataset_data_stream = self.dataset.get_data_stream()

        if fields:
            for required_field in ['_id', 'id', example_id_field]:
                if required_field not in fields:
                    fields.append(required_field)

        examples_data = app.db.TestExample.find(
            {'model_id': self.model_id, 'test_id': str(self._id)},
            fields
        )
        examples_data = dict([(epl['id'], epl)
                              for epl in examples_data])

        for row in dataset_data_stream:
            data = json.loads(row)
            example_id = data[example_id_field]
            example = examples_data.get(example_id)
            if not example:
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
class TestExample(Document):
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

    @property
    def data_input(self):
        if self['on_s3']:
            if not self['data_input'] and getattr(self, '_id'):
                data = self._load_from_s3()
                self['data_input'] = json.loads(data)
        return self['data_input']

    @data_input.setter
    def set_data_input(self, value):
        self['data_input'] = value

    def save(self, *args, **kwargs):
        data_input = None
        if self['data_input'] and self.on_s3:
            data_input = self['data_input']
            self['data_input'] = None
        super(TestExample, self).save(*args, **kwargs)
        if data_input:
            self._save_to_s3(data_input)

    def delete(self):
        helper = AmazonS3Helper()
        helper.delete_key(self.s3_key)
        super(TestExample, self).delete()


@app.conn.register
class Instance(Document):
    __collection__ = 'instances'
    structure = {
        'name': basestring,
        'description': basestring,
        'ip': basestring,
        'type': basestring,
        'is_default': bool,
        'created_on': datetime,
        'updated_on': datetime,
    }
    required_fields = ['name', 'created_on', 'updated_on', 'ip', ]
    default_values = {'created_on': datetime.utcnow,
                      'updated_on': datetime.utcnow,
                      'is_default': False, }
    use_dot_notation = True

    def __repr__(self):
        return '<Instance %r>' % self.name
