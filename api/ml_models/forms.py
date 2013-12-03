import json

from core.trainer.store import load_trainer
from core.trainer.trainer import Trainer, InvalidTrainerFile
from core.trainer.config import FeatureModel, SchemaException
from core.importhandler.importhandler import ExtractionPlan, \
    ImportHandlerException
from api.base.forms import BaseForm, ValidationError
from api.base.fields import ModelField, CharField, JsonField,\
    ImportHandlerFileField
from api.models import Tag, ImportHandler, Model


class ModelEditForm(BaseForm):
    name = CharField()
    train_import_handler = ModelField(model=ImportHandler, by_name=False,
                                         return_model=True)
    test_import_handler = ModelField(model=ImportHandler, by_name=False,
                                         return_model=True)
    example_id = CharField()
    example_label = CharField()
    tags = JsonField()

    def save(self, commit=True):
        old_tags = self.obj.tags
        model = super(ModelEditForm, self).save()

        if self.cleaned_data.get('tags', None):
            Tag.update_tags_count(old_tags, model.tags)

        return model


class ModelAddForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name',
                      ('test_import_handler', 'test_import_handler_file'))

    name = CharField()
    train_import_handler = ModelField(model=ImportHandler, by_name=False,
                                         return_model=True)
    train_import_handler_file = ImportHandlerFileField()
    test_import_handler = ModelField(model=ImportHandler, by_name=False,
                                         return_model=True)
    test_import_handler_file = ImportHandlerFileField()
    features = JsonField()
    trainer = CharField()

    #
    feature_model = None
    trainer_obj = None
    classifier_obj = None

    def clean_train_import_handler_file(self, value, field):
        self.cleaned_data['train_import_params'] = field.import_params
        return value

    def clean_test_import_handler_file(self, value, field):
        self.cleaned_data['test_import_params'] = field.import_params
        return value

    def clean_trainer(self, value, field):
        if value:
            try:
                # TODO: find a better way?
                value = value.encode('utf-8').replace('\r', '')
                self.trainer_obj = load_trainer(value)
                self.cleaned_data['status'] = Model.STATUS_TRAINED
                return self.trainer_obj
            except Exception as exc:
                raise ValidationError('Invalid trainer: {0!s}'.format(exc))

    def clean_features(self, value, field):
        if not value:
            return

        try:
            # TODO: add support of json dict to FeatureModel
            self.feature_model = FeatureModel(json.dumps(value), is_file=False)
        except SchemaException, exc:
            raise ValidationError('Invalid features: %s' % exc)
        return value

    def validate_data(self):
        if self.feature_model:
            if not (self.cleaned_data.get('train_import_handler_file', None) or \
                self.cleaned_data.get('train_import_handler', None) ):
                raise ValidationError('train_import_handler_file or \
train_import_handler should be specified for new model')
            self.trainer_obj = Trainer(self.feature_model)
        else:
            self.cleaned_data['trainer'] = None

    def save_importhandler(self, fieldname, name):
        data = self.cleaned_data.pop(fieldname, None)
        if data is not None:
            handler = ImportHandler()
            action = 'test' if fieldname.startswith('test') else 'train'
            handler.name = '%s handler for %s' % (name, action)
            handler.type = handler.TYPE_DB
            handler.import_params = self.cleaned_data.pop('%s_import_params' % action)
            handler.data = data
            handler.save()
            self.cleaned_data['%s_import_handler' % action] = handler

    def save(self, *args, **kwargs):
        name = self.cleaned_data['name']

        self.save_importhandler('train_import_handler_file', name)
        self.save_importhandler('test_import_handler_file', name)

        obj = super(ModelAddForm, self).save()
        # TODO: move it to model training for new models
        if self.trainer_obj:
            obj.set_trainer(self.trainer_obj)

        # TODO
        from api.features.models import FeatureSet, PredefinedClassifier
        features = self.cleaned_data['features']
        features_set = FeatureSet.from_model_features_dict(obj.name, features)
        obj.features_set = features_set
        classifier = PredefinedClassifier.from_model_features_dict(obj.name, features)
        obj.classifier = classifier.to_dict()
        obj.save()

        if obj.status == Model.STATUS_TRAINED:
            # Processing Model Parameters weights in celery task
            from api.tasks import fill_model_parameter_weights
            fill_model_parameter_weights.delay(str(obj.id))

        return obj
