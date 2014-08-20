import json
from api.base.forms.base_forms import BaseChooseInstanceAndDatasetMultiple
from api.import_handlers.models import DataSet
from api.instances.models import Instance
from api.servers.models import Server

from core.trainer.store import load_trainer
from core.trainer.trainer import Trainer, InvalidTrainerFile
from core.trainer.config import FeatureModel, SchemaException
from core.importhandler.importhandler import ExtractionPlan, \
    ImportHandlerException
from api.base.forms import BaseForm, ValidationError, ModelField, \
    CharField, JsonField, ImportHandlerFileField, \
    ChoiceField, ImportHandlerField, IntegerField
from api.models import Tag, ImportHandler, Model, XmlImportHandler
from api.features.models import FeatureSet, PredefinedClassifier
from api import app

db = app.sql_db


class ModelEditForm(BaseForm):
    name = CharField()
    train_import_handler = ImportHandlerField()
    test_import_handler = ImportHandlerField()
    example_id = CharField()
    example_label = CharField()
    tags = JsonField()

    def save(self, commit=True):
        old_tags = [t.text for t in self.obj.tags]
        model = super(ModelEditForm, self).save()

        tags = self.cleaned_data.get('tags', None)
        # TODO: refactor
        if tags:
            model.tags = []
            existing_tags = [t.text for t in Tag.query.all()]
            tags_to_create = list(set(tags) - set(existing_tags))
            for text in tags_to_create:
                tag = Tag()
                tag.text = text
                tag.count = 1
                tag.save()
            model.tags = Tag.query.filter(Tag.text.in_(tags)).all()
            model.save()
            for text in list(set(tags + old_tags) - set(tags_to_create)):
                tag = Tag.query.filter_by(text=text).one()
                tag.count = len(tag.models)
                tag.save()

        return model


class ModelAddForm(BaseForm):
    """
    Adds new model.

    Note: If import handler and import handler file would be specified,
    new model will use import handler from file.
    """
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name',
                       ('import_handler', 'import_handler_file'))

    name = CharField()
    import_handler = ImportHandlerField()
    import_handler_file = ImportHandlerFileField()
    test_import_handler = ImportHandlerField()
    test_import_handler_file = ImportHandlerFileField()
    features = JsonField()
    trainer = CharField()

    def clean_name(self, value, field):
        if not value:
            raise ValidationError('specify name of the model')

        count = Model.query.filter_by(name=value).count()
        if count:
            raise ValidationError(
                'Model with name "%s" already exist. Please choose another one.' % value)

        return value

    def clean_import_handler(self, value, field):
        self.cleaned_data['train_import_handler'] = value
        return value

    def clean_import_handler_file(self, value, field):
        self.cleaned_data['train_import_params'] = field.import_params
        self.train_import_handler_type = field.import_handler_type
        return value

    def clean_test_import_handler_file(self, value, field):
        self.cleaned_data['test_import_params'] = field.import_params
        self.test_import_handler_type = field.import_handler_type
        return value

    def clean_features(self, value, field):
        if value:
            try:
                # TODO: add support of json dict to FeatureModel
                feature_model = FeatureModel(json.dumps(value), is_file=False)
                self.cleaned_data['trainer'] = Trainer(feature_model)
            except SchemaException, exc:
                raise ValidationError(
                    'Features JSON file is invalid: %s' % exc)
        return value

    def clean_trainer(self, value, field):
        if value:
            try:
                # TODO: find a better way?
                value = value.encode('utf-8').replace('\r', '')
                trainer_obj = load_trainer(value)
                self.cleaned_data['status'] = Model.STATUS_TRAINED
                return trainer_obj
            except Exception as exc:
                raise ValidationError(
                    'Pickled trainer model is invalid: {0!s}'.format(exc))

    def save(self, *args, **kwargs):
        name = self.cleaned_data['name']
        created_handlers = []
        try:
            if self.cleaned_data.get('import_handler_file'):
                created_handlers.append(self._save_importhandler(
                    'import_handler_file', name,
                    handler_type=self.train_import_handler_type))
            if self.cleaned_data.get('test_import_handler_file'):
                created_handlers.append(self._save_importhandler(
                    'test_import_handler_file', name,
                    handler_type=self.test_import_handler_type))
            if not 'test_import_handler' in self.cleaned_data:
                self.cleaned_data['test_import_handler'] = \
                    self.cleaned_data['train_import_handler']

            model = super(ModelAddForm, self).save(commit=False)
            trainer = self.cleaned_data.get('trainer')
            if trainer:
                model.set_trainer(trainer)
            features = self.cleaned_data.get('features')
            if features:
                model.features_set.from_dict(features, commit=False)
                model.classifier = features['classifier']
        except Exception, exc:
            db.session.rollback()
            for handler in created_handlers:
                db.session.delete(handler)
                db.session.commit()
            raise
        else:
            db.session.commit()
        if model.status == Model.STATUS_TRAINED:
            from api.ml_models.tasks import fill_model_parameter_weights
            model.create_segments(trainer._get_segments_info())

            for segment in model.segments:
                fill_model_parameter_weights.delay(model.id, segment.id)


        return model

    def _save_importhandler(self, fieldname, name, handler_type='json'):
        """
        Adds new import handler to the system,
        if it was specified in file field.
        Use it in the model.
        """
        def determine_name(name, action):
            if action == 'train':
                name = "%s import handler" % name
            else:
                name = "%s test import handler" % name

            while True:
                count = ImportHandler.query.filter_by(name=name).count()
                if not count:
                    return name
                name += '_'

            return name

        data = self.cleaned_data.pop(fieldname, None)
        if data is not None:
            if handler_type == 'xml':
                from api.import_handlers.models import XmlImportHandler
                cls = XmlImportHandler
            else:
                cls = ImportHandler

            handler = cls()
            action = 'test' if fieldname.startswith('test') else 'train'
            handler.name = determine_name(name, action)
            handler.import_params = self.cleaned_data.pop(
                '%s_import_params' % action)
            handler.data = data
            self.cleaned_data['%s_import_handler' % action] = handler
            db.session.add(handler)
            db.session.commit()
            return handler


class ModelTrainForm(BaseChooseInstanceAndDatasetMultiple):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('obj', None)
        super(ModelTrainForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.obj.status = Model.STATUS_QUEUED
        self.obj.save()
        return self.obj


class TransformDataSetForm(BaseForm):
    required_fields = ('dataset',)
    dataset = ModelField(model=DataSet, return_model=True)