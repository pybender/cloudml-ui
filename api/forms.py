import json
from datetime import datetime
from flask import request

from api import app
from api.resources import ValidationError
from api.models import Model
from core.trainer.store import load_trainer
from core.trainer.trainer import Trainer, InvalidTrainerFile
from core.trainer.config import FeatureModel, SchemaException
from core.importhandler.importhandler import ExtractionPlan, \
    ImportHandlerException


class BaseForm():
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
        for name in self.fields:
            print name
            value = self.data.get(name, None)
            mthd = "clean_%s" % name
            if hasattr(self, mthd):
                value = getattr(self, mthd)(value)
            if value:
                self.cleaned_data[name] = value
        self.validate_obj()
        self._cleaned = True
        print self.cleaned_data.keys()
        return self.cleaned_data

    def save(self, commit=True):
        if not self.is_valid():
            raise ValidationError(self.errors)

        for name, val in self.cleaned_data.iteritems():
            setattr(self.obj, name, val)

        self.updated_on = datetime.now()
        if commit:
            self.obj.save(validate=True)

        return self.obj

    def validate_obj(self):
        pass


class ModelEditForm(BaseForm):
    fields = ('importhandler', 'train_importhandler',
              'example_id', 'example_label', 'name')

    def clean_importhandler(self, value):
        if value and not value == 'undefined':
            return json.loads(value)

    clean_train_importhandler = clean_importhandler


class ModelAddForm(BaseForm):
    fields = ('features', 'trainer', 'train_importhandler',
              'name', 'importhandler')
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

    def clean_train_importhandler(self, value):
        return self._clean_json_val('train_importhandler', value)

    def clean_importhandler(self, value):
        loaded_value = self._clean_json_val('importhandler', value)
        if not loaded_value:
            raise ValidationError('importhandler is required')

        try:
            plan = ExtractionPlan(value, is_file=False)
            self.cleaned_data['import_params'] = plan.input_params
        except (ValueError, ImportHandlerException) as exc:
            raise ValidationError('Invalid importhandler: %s' % exc)
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


class ImportHandlerAddForm(BaseForm):
    fields = ('name', 'type', 'data', 'import_params', )

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

    def clean_type(self, value):
        # if not type in ImportHandler.TYPE_CHOICES:
        #     raise ValidationError('invalid')
        return value

    def clean_data(self, value):
        if not value:
            raise ValidationError('data is required')

        try:
            data = json.loads(value)
        except ValueError, exc:
            raise ValidationError('Invalid data: %s' % exc)

        plan = ExtractionPlan(value, is_file=False)
        self.cleaned_data['import_params'] = plan.input_params
        return data


class AddTestForm(BaseForm):
    fields = ('name', 'model', 'parameters', 'instance', )

    def clean_name(self, value):
        total = app.db.Test.find({'model_id': self.model_id}).count()
        return "Test%s" % (total + 1)

    def clean_model(self, value):
        from bson.objectid import ObjectId
        self.model = app.db.Model.find_one({'_id': ObjectId(self.model_id)})
        if self.model is None:
            raise ValidationError('Model not found')

        self.cleaned_data['model_name'] = self.model.name
        self.cleaned_data['model_id'] = self.model_id
        return self.model

    def clean_instance(self, value):
        from bson.objectid import ObjectId
        return app.db.Instance.find_one({'_id': ObjectId(value)})

    def clean_parameters(self, value):
        parser = populate_parser(self.model)
        return parser.parse_args()

    def save(self):
        test = BaseForm.save(self, commit=False)
        test.status = test.STATUS_QUEUED
        test.save(check_keys=False)

        from api.tasks import run_test
        instance = self.cleaned_data['instance']
        run_test.apply_async(args=[str(test._id)],
                             queue=instance.name,
                             routing_key='%s.run_test' % instance.name)
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


def populate_parser(model):
    from flask.ext.restful import reqparse
    parser = reqparse.RequestParser()
    for param in model.import_params:
        parser.add_argument(param, type=str)
    return parser
