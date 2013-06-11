import json
from datetime import datetime
from flask import request
from bson.objectid import ObjectId

from api import app
from api.resources import ValidationError
from api.models import Model
from core.trainer.store import load_trainer
from core.trainer.trainer import Trainer, InvalidTrainerFile
from core.trainer.config import FeatureModel, SchemaException
from core.importhandler.importhandler import ExtractionPlan, \
    ImportHandlerException


class BaseForm(object):
    def __init__(self, data=None, obj=None, Model=None, **kwargs):
        if data is None:
            data = {}
            for k in request.form.keys():
                data[k] = request.form.get(k, None)
            for k in request.files.keys():
                data[k] = request.files.get(k, None)

        self.data = data
        self.errors = []
        if obj:
            self.obj = obj
        elif Model:
            self.obj = Model()
        else:
            raise Exception('Spec obj or Model')
        self._cleaned = False

        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    @property
    def error_messages(self):
        return ','.join(self.errors)

    def is_valid(self):
        if not self._cleaned:
            self.clean()
        return not bool(self.errors)

    def clean(self):
        self.cleaned_data = {}
        if isinstance(self.fields, dict):
            fields = self.fields
        else:
            fields = dict([(name, False) for name in self.fields])

        for name, required in fields.iteritems():
            value = self.data.get(name, None)
            mthd = "clean_%s" % name
            if hasattr(self, mthd):
                value = getattr(self, mthd)(value)
            if value:
                self.cleaned_data[name] = value
            elif required:
                cleaned_value = self.cleaned_data.get(name)
                if not cleaned_value:
                    raise ValidationError('%s is required' % name)

        self.validate_obj()
        self._cleaned = True
        return self.cleaned_data

    def save(self, commit=True):
        if not self.is_valid():
            raise ValidationError(self.errors)

        for name, val in self.cleaned_data.iteritems():
            setattr(self.obj, name, val)

        self.obj.updated_on = datetime.now()
        if commit:
            self.obj.save(validate=True)

        return self.obj

    def validate_obj(self):
        pass


class BaseModelForm(BaseForm):
    def _clean_importhandler(self, value):
        if value and not value == 'undefined':
            obj = app.db.ImportHandler.find_one({'_id': ObjectId(value)})
            print type(obj)
            if obj is not None:
                return obj

    clean_train_import_handler = _clean_importhandler
    clean_test_import_handler = _clean_importhandler


class ModelEditForm(BaseModelForm):
    fields = ('test_import_handler', 'train_import_handler',
              'example_id', 'example_label', 'name')


class ModelAddForm(BaseModelForm):
    fields = ('features', 'trainer', 'train_import_handler',
              'name', 'test_import_handler')
    trainer = None

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

    def clean_trainer(self, value):
        if value:
            try:
                self.trainer = load_trainer(value)
            except InvalidTrainerFile, exc:
                raise ValidationError('Invalid trainer: %s' % exc)

    def clean_features(self, value):
        loaded_value = self._clean_json_val('features', value)
        if loaded_value:
            try:
                self.feature_model = FeatureModel(value, is_file=False)
            except SchemaException, exc:
                raise ValidationError('Invalid features: %s' % exc)

        return loaded_value

    def validate_obj(self):
        features = self.cleaned_data.get('features')
        if not features and not self.trainer:
            raise ValidationError('Either features, either pickled \
trained model is required for posting model')

        if features:
            self.trainer = Trainer(self.feature_model)
        else:
            self.cleaned_data['status'] = Model.STATUS_TRAINED

    def save(self):
        obj = BaseForm.save(self)
        obj.set_trainer(self.trainer)
        if obj.status == Model.STATUS_TRAINED:
            # Processing Model Parameters weights in celery task
            from api.tasks import fill_model_parameter_weights
            fill_model_parameter_weights.delay(str(obj._id))
        obj.save()
        return obj

    def _clean_json_val(self, name, value):
        if value:
            try:
                return json.loads(value)
            except (ValueError), exc:
                raise ValidationError('Invalid %s: %s %s' % (name, value, exc))
            except TypeError:
                return {}


class BaseChooseInstanceAndDataset(BaseForm):
    HANDLER_TYPE = 'train'

    fields = ['aws_instance', 'dataset', 'parameters']

    def clean_parameters(self, value):
        self.params_filled = False
        handler = getattr(self.model, '%s_import_handler' % self.HANDLER_TYPE)
        self.parameter_names = handler['import_params']
        parser = populate_parser(self.parameter_names)
        params = parser.parse_args()

        parameters = {}
        missed_params = []
        for name, val in params.iteritems():
            if not val:
                missed_params.append(name)
            else:
                parameters[name] = val
                self.params_filled = True

        if self.params_filled and missed_params:
            raise ValidationError('Parameters %s are required' % ', '.join(missed_params))

        return parameters

    def clean_dataset(self, value):
        if value:
            ds = app.db.DataSet.find_one({'_id': ObjectId(value)})
            if ds is None:
                raise ValidationError('DataSet not found')
            return ds

    def clean_aws_instance(self, value):
        instance = app.db.Instance.find_one({'_id': ObjectId(value)})
        if instance is None:
            raise ValidationError('Instance is required')
        return instance

    def validate_obj(self):
        ds = self.cleaned_data.get('dataset', None)
        if not (self.params_filled or ds):
            raise ValidationError('Parameters (%s) or \
dataset are required' % ', '.join(self.parameter_names))


class ModelTrainForm(BaseChooseInstanceAndDataset):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('obj', None)
        super(ModelTrainForm, self).__init__(*args, **kwargs)

    def save(self):
        self.obj.status = self.obj.STATUS_QUEUED
        self.obj.save()
        return self.obj


class BaseImportHandlerForm(BaseForm):
    def clean_data(self, value):
        if not value:
            return

        try:
            data = json.loads(value)
        except ValueError, exc:
            raise ValidationError('Invalid data: %s' % exc)

        try:
            plan = ExtractionPlan(value, is_file=False)
            self.cleaned_data['import_params'] = plan.input_params
        except (ValueError, ImportHandlerException) as exc:
            raise ValidationError('Invalid importhandler: %s' % exc)

        return data


class ImportHandlerEditForm(BaseImportHandlerForm):
    fields = ('data', 'name')


class ImportHandlerAddForm(BaseImportHandlerForm):
    fields = {'name': True,
              'type': True,
              'data': True,
              'import_params': True}

    def clean_type(self, value):
        # if not type in ImportHandler.TYPE_CHOICES:
        #     raise ValidationError('invalid')
        return value


class AddTestForm(BaseChooseInstanceAndDataset):
    HANDLER_TYPE = 'test'

    fields = ['name', 'model', ] + BaseChooseInstanceAndDataset.fields

    def clean_name(self, value):
        total = app.db.Test.find({'model_id': self.model_id}).count()
        return "Test%s" % (total + 1)

    def clean_model(self, value):
        self.model = app.db.Model.find_one({'_id': ObjectId(self.model_id)})
        if self.model is None:
            raise ValidationError('Model not found')

        self.cleaned_data['model_name'] = self.model.name
        self.cleaned_data['model_id'] = self.model_id
        return self.model

    def save(self):
        test = BaseForm.save(self, commit=False)
        test.status = test.STATUS_QUEUED
        test.save(check_keys=False)

        from api.tasks import run_test, import_data
        instance = self.cleaned_data['aws_instance']

        if self.params_filled:
            # load and train
            from api.models import ImportHandler
            import_handler = ImportHandler(test.model.test_import_handler)
            params = self.cleaned_data.get('parameters', None)
            dataset = import_handler.create_dataset(params)
            import_data.apply_async((str(dataset._id), ),
                                    link=run_test.subtask(args=(str(test._id), ),
                                    options={'queue':instance['name']}))
        else:
            # test using dataset
            dataset = self.cleaned_data.get('dataset', None)
            run_test.apply_async((str(dataset._id),
                                  str(test._id),),
                                  queue=instance['name'])

        return test


class InstanceAddForm(BaseForm):
    fields = ('name', 'description', 'ip', 'type', 'is_default', )

    def clean_is_default(self, value):
        return value == 'true'

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

    def clean_type(self, value):
        # if not type in ImportHandler.TYPE_CHOICES:
        #     raise ValidationError('invalid')
        return value

    def clean_ip(self, value):
        if not value:
            raise ValidationError('data is required')
        return value

    def save(self):
        instance = BaseForm.save(self)
        if instance.is_default:
            instances = app.db.Instance.collection
            instances.update({'_id': {'$ne': instance._id}},
                             {"$set": {"is_default": False}},
                             multi=True, safe=True)
        return instance


class InstanceEditForm(BaseForm):
    fields = ('name', 'is_default', )

    def clean_is_default(self, value):
        return value == 'true'

    def _field_changed(self, name):
        return getattr(self.obj, name) != self.cleaned_data[name]

    def save(self):
        default_changed = self._field_changed('is_default')
        instance = BaseForm.save(self)
        if default_changed:
            instances = app.db.Instance.collection
            instances.update({'_id': {'$ne': instance._id}},
                             {"$set": {"is_default": False}},
                             multi=True, safe=True)
        return instance


def populate_parser(import_params):
    from flask.ext.restful import reqparse
    parser = reqparse.RequestParser()
    for param in import_params:
        parser.add_argument(param, type=str)
    return parser
