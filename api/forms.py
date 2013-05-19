import json
from datetime import datetime

from api.resources import ValidationError
from api.models import Model


class BaseForm():
    def __init__(self, data, obj=None, Model=None):
        self.data = data
        self.errors = []
        if obj:
            self.obj = obj
        elif Model:
            self.obj = Model()
        else:
            raise Exception('Spec obj or Model')
        self._cleaned = False

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
            value = self.data.get(name, None)
            mthd = "clean_%s" % name
            if hasattr(self, mthd):
                value = getattr(self, mthd)(value)
            if value:
                self.cleaned_data[name] = value
        self.validate_obj()
        self._cleaned = True
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
              'example_id', 'example_label')

    def clean_importhandler(self, value):
        if value and not value == 'undefined':
            return json.loads(value)

    clean_train_importhandler = clean_importhandler


from core.trainer.store import load_trainer
from core.trainer.trainer import Trainer, InvalidTrainerFile
from core.trainer.config import FeatureModel, SchemaException
from core.importhandler.importhandler import ExtractionPlan, \
    ImportHandlerException


class ModelAddForm(BaseForm):
    fields = ('features', 'trainer', 'train_importhandler',
              'name', 'importhandler')

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

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
        trainer = self.cleaned_data.get('trainer')
        if not features and not trainer:
            raise ValidationError('Either features, either pickled \
trained model is required for posting model')

        if features:
            self.trainer = Trainer(self.feature_model)
        else:
            try:
                self.trainer = load_trainer(trainer)
            except InvalidTrainerFile, exc:
                raise ValidationError('Invalid trainer: %s' % exc)
            self.cleaned_data['status'] = Model.STATUS_TRAINED

    def save(self):
        obj = BaseForm.save(self)
        obj.set_trainer(self.trainer)
        if obj.status == Model.STATUS_TRAINED:
            # Processing Model Parameters weights in celery task
            from api.tasks import fill_model_parameter_weights
            fill_model_parameter_weights.delay(str(obj._id),
                                               **self.trainer.get_weights())
        obj.save()
        return obj

    def _clean_json_val(self, name, value):
        if value and not value == 'undefined':
            try:
                return json.loads(value)
            except ValueError, exc:
                raise ValidationError('Invalid %s: %s %s' % (name, value, exc))
