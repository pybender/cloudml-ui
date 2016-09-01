"""
Model and Transformer specific forms.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import importlib

from api import app
from api.base.forms.base_forms import BaseChooseInstanceAndDatasetMultiple, \
    ParametersConvertorMixin
from api.import_handlers.models import DataSet
from api.base.forms import BaseForm, ValidationError, ModelField, \
    CharField, JsonField, ImportHandlerFileField, UniqueNameField, \
    ChoiceField, ImportHandlerField, IntegerField, BooleanField, FeaturesField
from api.models import Tag, Model, XmlImportHandler, \
    Transformer, BaseTrainedEntity, ClassifierGridParams
from api.features.models import Feature
from cloudml.trainer.transformers import TRANSFORMERS
from api.features.config import CLASSIFIERS

db = app.sql_db


class ModelEditForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', )
    name = CharField()
    train_import_handler = ImportHandlerField()
    test_import_handler = ImportHandlerField()
    example_id = CharField()
    example_label = CharField()
    tags = JsonField()
    features = FeaturesField()

    def save(self, commit=True):
        old_tags = [tag for tag in self.obj.tags]
        old_tags_texts = [t.text for t in self.obj.tags]
        model = super(ModelEditForm, self).save()

        tags = self.cleaned_data.get('tags', None)
        if tags:
            for tag_text in tags:
                if tag_text not in old_tags_texts:
                    t = Tag.query.filter_by(text=tag_text).all()
                    if len(t):
                        new_tag = t[0]
                    else:
                        new_tag = Tag()
                        new_tag.text = tag_text
                        new_tag.save()
                    old_tags.append(new_tag)

            model.tags = [tag for tag in old_tags if tag.text in tags]
            model.save()
            for tag in old_tags:
                tag.update_counter()

        features = self.cleaned_data.get('features', None)
        if features:
            try:
                Feature.query.filter_by(
                    feature_set_id=model.features_set_id).delete()
                model.classifier = features['classifier'] or {}
                model.features_set.from_dict(features, commit=False)
            except Exception as e:
                db.session.rollback()
                raise Exception("Error occurred while updating features: "
                                "{0}".format(e))
            else:
                db.session.commit()

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

    name = UniqueNameField(Model=Model)
    import_handler = ImportHandlerField()
    import_handler_file = ImportHandlerFileField()
    test_import_handler = ImportHandlerField()
    test_import_handler_file = ImportHandlerFileField()
    features = JsonField()
    trainer = CharField()

    def clean_import_handler(self, value, field):
        self.cleaned_data['train_import_handler'] = value
        return value

    def clean_import_handler_file(self, value, field):
        self.cleaned_data['train_import_params'] = field.import_params
        return value

    def clean_test_import_handler_file(self, value, field):
        self.cleaned_data['test_import_params'] = field.import_params
        return value

    def clean_features(self, value, field):
        if value:
            from cloudml.trainer.trainer import Trainer
            from cloudml.trainer.config import FeatureModel, SchemaException
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
                from cloudml.trainer.store import load_trainer
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
                    'import_handler_file', name))
            if self.cleaned_data.get('test_import_handler_file'):
                created_handlers.append(self._save_importhandler(
                    'test_import_handler_file', name))
            if 'test_import_handler' not in self.cleaned_data:
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
            from api.ml_models.tasks import visualize_model
            model.create_segments(trainer._get_segments_info())

            for segment in model.segments:
                visualize_model.delay(model.id, segment.id)

        return model

    def _save_importhandler(self, fieldname, name, handler_type='xml'):
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
                count = XmlImportHandler.query.filter_by(name=name).count()
                if not count:
                    return name
                name += '_'

            return name

        data = self.cleaned_data.pop(fieldname, None)
        if data is not None:
            if handler_type == 'xml':
                from api.import_handlers.models import XmlImportHandler
                cls = XmlImportHandler

            handler = cls()
            action = 'test' if fieldname.startswith('test') else 'train'
            handler.name = determine_name(name, action)
            handler.import_params = self.cleaned_data.pop(
                '%s_import_params' % action)
            handler._set_user()
            try:
                handler.data = data
            except Exception, exc:
                self.add_error('fields', str(exc))
                raise ValidationError(self.error_messages, errors=self.errors)
            self.cleaned_data['%s_import_handler' % action] = handler
            db.session.add(handler)
            db.session.commit()
            return handler


class TrainForm(BaseChooseInstanceAndDatasetMultiple):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('obj', None)
        super(TrainForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.obj.status = BaseTrainedEntity.STATUS_QUEUED
        self.obj.save()
        return self.obj


class TransformDataSetForm(BaseForm):
    required_fields = ('dataset',)
    dataset = ModelField(model=DataSet, return_model=True)


class TransformersDownloadForm(BaseForm):
    required_fields = ('segment', 'data_format')
    segment = CharField()
    data_format = ChoiceField(choices=['csv', 'json'])


class TransformerForm(BaseForm, ParametersConvertorMixin):
    """
    Adds/Edits Pretrained transformer form
    """
    NO_REQUIRED_FOR_EDIT = True
    REQUIRED_FIELDS = ['train_import_handler']
    FORM_REQUIRED_FIELDS = REQUIRED_FIELDS + \
        ['name', 'type', 'feature_type', 'field_name']
    group_chooser = 'json_selected'
    required_fields_groups = {'true': REQUIRED_FIELDS + ['json'],
                              'false': FORM_REQUIRED_FIELDS,
                              None: FORM_REQUIRED_FIELDS}

    name = CharField()
    feature_type = CharField()
    field_name = CharField()
    type_field = ChoiceField(
        choices=Transformer.TYPES_LIST, name='type')
    params = JsonField()
    json = JsonField()
    json_selected = BooleanField()
    train_import_handler = ImportHandlerField()

    def validate_data(self):
        name = self.cleaned_data.get('name')
        json_selected = self.cleaned_data.get('json_selected')
        if json_selected:
            json = self.cleaned_data.get('json')
            name = json['transformer-name']
            params = json['transformer'].get('params')
            type_ = json['transformer'].get('type')
            self.is_name_available(name, field_name='json')
        else:
            self.is_name_available(name)
            params = self.cleaned_data.get('params')
            type_ = self.cleaned_data.get('type')

        self.convert_params(type_, params, configuration=TRANSFORMERS)

    def save(self, commit=True):
        if self.cleaned_data.get('json_selected'):
            json = self.cleaned_data['json']
            transformer = Transformer()
            transformer.load_from_json(json)
            transformer.train_import_handler = \
                self.cleaned_data['train_import_handler']
            transformer.save(commit=commit)
            return transformer
        else:
            return super(TransformerForm, self).save(commit)

    def is_name_available(self, name, field_name='name'):
        if self.obj and self.obj.id:
            return True  # edit

        if Transformer.query.filter_by(name=name).count():
            self.add_error(field_name, 'Transformer with name {0} \
already exist'.format(name))
            return False
        return True


class FeatureTransformerForm(BaseForm, ParametersConvertorMixin):
    """
    Adds/edits feature transformer form.
    """
    group_chooser = 'predefined_selected'
    REQUIRED_FORM = ['type']
    REQUIRED_PRETRAINED = ['transformer']
    required_fields_groups = {
        'true': REQUIRED_PRETRAINED,
        'false': REQUIRED_FORM,
        None: REQUIRED_FORM}

    predefined_selected = BooleanField()
    feature_id = ModelField(model=Feature, return_model=True)

    type_field = CharField(name='type')
    params = JsonField()

    transformer = ModelField(model=Transformer, return_model=True)

    def validate_data(self):
        type_ = self.cleaned_data.get('type')
        pretrained_selected = self.cleaned_data.get('predefined_selected')
        if not pretrained_selected and type_ not in Transformer.TYPES_LIST:
            self.add_error('type', 'type is invalid')
            return

        self.convert_params(type_, self.cleaned_data.get('params'),
                            configuration=TRANSFORMERS)

    def save(self, commit=True, save=True):
        feature = self.cleaned_data.get('feature_id', None)
        is_pretrained = self.cleaned_data.get('predefined_selected', False)
        if is_pretrained:
            pretrained_transformer = self.cleaned_data.get('transformer')
            transformer = {'type': pretrained_transformer.name,
                           'id': pretrained_transformer.id}
        else:
            transformer = {
                'id': -1,
                "type": self.cleaned_data.get('type'),
                "params": self.cleaned_data.get('params')
            }
        if feature is not None:
            feature.transformer = transformer
            feature.save()
        return transformer


class GridSearchForm(BaseForm):
    parameters = JsonField()
    scoring = CharField()
    train_dataset = ModelField(model=DataSet, return_model=True)
    test_dataset = ModelField(model=DataSet, return_model=True)

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('model', None)
        super(GridSearchForm, self).__init__(*args, **kwargs)

    def clean_parameters(self, grid_params, field):
        params = {}
        config = CLASSIFIERS[self.model.classifier['type']]
        config_params = config['parameters']
        for pconfig in config_params:
            name = pconfig['name']
            if name in grid_params:
                value = grid_params[name]
                if not value:
                    continue

                value = value.split(',')
                type_ = pconfig.get('type', 'string')
                if type_ == 'integer':
                    value = [int(item) for item in value]
                elif type_ == 'float':
                    value = [float(item) for item in value]
                elif type_ == 'boolean':
                    value = [item == 'true' for item in value]

                choices = pconfig.get('choices')
                if choices:
                    for item in value:
                        if item not in choices:
                            raise ValidationError(
                                'Invalid {0}: should be one of {1}'.format(
                                    name, ','.join(choices)))

                params[name] = value
        return params

    def save(self, *args, **kwargs):
        obj = super(GridSearchForm, self).save(commit=False)
        obj.model = self.model
        obj.save()
        return obj


class VisualizationOptionsForm(BaseForm):
    """
    Form used for updating Trained model visualization.

    Note:
        Now it support only `tree_deep` type for Decision Tree and
        Random Forest classifiers.
    """
    UPDATE_TREE_DEEP = 'tree_deep'
    TYPES = [UPDATE_TREE_DEEP, ]
    PARAMS_BY_TYPE = {UPDATE_TREE_DEEP: [{'name': 'deep', 'type': 'int'}]}

    parameters = JsonField()
    type_ = CharField(name="type")

    def __init__(self, *args, **kwargs):
        super(VisualizationOptionsForm, self).__init__(*args, **kwargs)

    def clean_type(self, value, field):
        if value and value not in self.TYPES:
            raise ValidationError('invalid type')
        return value

    def validate_data(self):
        type_ = self.cleaned_data.get('type')
        parameters = self.cleaned_data.get('parameters')
        config = self.PARAMS_BY_TYPE[type_]
        for item in config:
            name = item['name']
            val = parameters.get(name)
            if not val:
                self.add_error('parameters', 'Parameter %s is required' % name)
            if item['type'] == 'int':
                try:
                    parameters[name] = int(val)
                except Exception, exc:
                    self.add_error(
                        'parameters',
                        "Can't parse parameter %s: %s" % (name, exc))

    def process(self):
        type_ = self.cleaned_data.get('type')
        try:
            self.obj.visualize_model(status='queued')
            getattr(self, "process_%s" % type_)()
        except Exception, exc:
            self.obj.visualize_model(status='error: %s' % exc)

    def process_tree_deep(self):
        from tasks import generate_visualization_tree
        parameters = self.cleaned_data.get('parameters')
        generate_visualization_tree.delay(self.obj.id, parameters['deep'])


class ModelPartsSizeCalculationForm(BaseForm):
    required_fields = ('deep')
    deep = IntegerField()

    def clean_deep(self, value, field):
        try:
            val = int(value)
            if val < 1:
                raise ValidationError('deep should be positive value')
            return val
        except Exception, exc:
            raise ValidationError("Can't parse deep parameter: {}"
                                  .format(exc.message))

    def process(self):
        from tasks import calculate_model_parts_size
        deep = self.cleaned_data.get('deep')
        calculate_model_parts_size.delay(self.obj.id, deep)
