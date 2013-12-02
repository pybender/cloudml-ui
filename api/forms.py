from compiler.transformer import Transformer
import json
from datetime import datetime
from api.features.models import Feature
from flask import request
from bson.objectid import ObjectId

from api import app
from api.resources import ValidationError, NotFound
from api.features.models import FeatureSet
from api.models import DataSet
from api.base.forms import BaseForm as BaseFormEx
from api.base.fields import *
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
        errors = ', '.join(["%s%s" % (err['name'] + ': ' if err['name'] else '', err['error'])
                           for err in self.errors])
        return 'Here is some validation errors: %s' % errors

    def is_valid(self):
        if not self._cleaned:
            self.clean()
        return not bool(self.errors)

    def before_clean(self):
        pass

    def clean(self):
        self.cleaned_data = {}
        self.before_clean()
        if isinstance(self.fields, dict):
            fields = self.fields
        else:
            fields = dict([(name, False) for name in self.fields])
        for name, required in fields.iteritems():
            value = self.data.get(name, None)
            mthd = "clean_%s" % name
            if hasattr(self, mthd):
                try:
                    value = getattr(self, mthd)(value)
                except ValidationError, exc:
                    self.errors.append({'name': name, 'error': str(exc)})
            if value is not None:
                self.cleaned_data[name] = value
            elif required:
                cleaned_value = self.cleaned_data.get(name)
                if not cleaned_value:
                    self.errors.append({'name': name, 'error': '%s is required'})

        try:
            self.validate_obj()
        except ValidationError, exc:
            self.errors.append({'name': None, 'error': str(exc)})

        if self.errors:
            raise ValidationError(self.error_messages, errors=self.errors)

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

    def _clean_document(self, value, Document, name, by_id=True):
        if value:
            if by_id:
                obj = Document.get_from_id(ObjectId(value))
            else:
                obj = Document.find_one({'name': value})
            if not obj:
                raise ValidationError('%s not found' % name)

            return obj


# class BaseModelForm(BaseForm):
#     def _clean_importhandler(self, value):
#         if value and not value == 'undefined':
#             return app.db.ImportHandler.find_one({'_id': ObjectId(value)})

#     clean_train_import_handler = _clean_importhandler
#     clean_test_import_handler = _clean_importhandler


# class ModelEditForm(BaseModelForm):
#     fields = ('test_import_handler', 'train_import_handler',
#               'example_id', 'example_label', 'name', 'tags')

#     def clean_tags(self, value):
#         if not value:
#             return None
#         return json.loads(value)

#     def save(self, commit=True):
#         old_tags = self.obj.tags
#         model = super(ModelEditForm, self).save()

#         if self.cleaned_data.get('tags', None):
#             app.db.Tag.update_tags_count(old_tags, model.tags)

#         return model


# class ModelEditForm(BaseFormEx):
#     name = CharField()
#     train_import_handler = DocumentField(doc='ImportHandler', by_name=False,
#                                          return_doc=True)
#     test_import_handler = DocumentField(doc='ImportHandler', by_name=False,
#                                          return_doc=True)
#     example_id = CharField()
#     example_label = CharField()
#     tags = JsonField()
#
#     def save(self, commit=True):
#         old_tags = self.obj.tags
#         model = super(ModelEditForm, self).save()
#
#         if self.cleaned_data.get('tags', None):
#             app.db.Tag.update_tags_count(old_tags, model.tags)
#
#         return model
#
#
# class ModelAddForm(BaseFormEx):
#     NO_REQUIRED_FOR_EDIT = True
#     required_fields = ('name',
#                       ('test_import_handler', 'test_import_handler_file'))
#
#     name = CharField()
#     train_import_handler = DocumentField(doc='ImportHandler', by_name=False,
#                                          return_doc=True)
#     train_import_handler_file = ImportHandlerFileField()
#     test_import_handler = DocumentField(doc='ImportHandler', by_name=False,
#                                          return_doc=True)
#     test_import_handler_file = ImportHandlerFileField()
#     features = JsonField()
#     trainer = CharField()
#
#     #
#     feature_model = None
#     trainer_obj = None
#     classifier_obj = None
#
#     def clean_train_import_handler_file(self, value, field):
#         self.cleaned_data['train_import_params'] = field.import_params
#         return value
#
#     def clean_test_import_handler_file(self, value, field):
#         self.cleaned_data['test_import_params'] = field.import_params
#         return value
#
#     def clean_trainer(self, value, field):
#         if value:
#             try:
#                 # TODO: find a better way?
#                 value = value.encode('utf-8').replace('\r', '')
#                 self.trainer_obj = load_trainer(value)
#                 self.cleaned_data['status'] = Model.STATUS_TRAINED
#                 return self.trainer_obj
#             except Exception as exc:
#                 raise ValidationError('Invalid trainer: {0!s}'.format(exc))
#
#     def clean_features(self, value, field):
#         if not value:
#             return
#
#         try:
#             # TODO: add support of json dict to FeatureModel
#             self.feature_model = FeatureModel(json.dumps(value), is_file=False)
#         except SchemaException, exc:
#             raise ValidationError('Invalid features: %s' % exc)
#         return value
#
#     def validate_data(self):
#         if self.feature_model:
#             if not (self.cleaned_data.get('train_import_handler_file', None) or \
#                 self.cleaned_data.get('train_import_handler', None) ):
#                 raise ValidationError('train_import_handler_file or \
# train_import_handler should be specified for new model')
#             self.trainer_obj = Trainer(self.feature_model)
#         else:
#             self.cleaned_data['trainer'] = None
#
#     def save_importhandler(self, fieldname, name):
#         data = self.cleaned_data.pop(fieldname, None)
#         if data is not None:
#             handler = app.db.ImportHandler()
#             action = 'test' if fieldname.startswith('test') else 'train'
#             handler.name = '%s handler for %s' % (name, action)
#             handler.type = handler.TYPE_DB
#             handler.import_params = self.cleaned_data.pop('%s_import_params' % action)
#             handler.data = data
#             handler.save()
#             self.cleaned_data['%s_import_handler' % action] = handler
#
#     def save(self, *args, **kwargs):
#         name = self.cleaned_data['name']
#
#         self.save_importhandler('train_import_handler_file', name)
#         self.save_importhandler('test_import_handler_file', name)
#
#         obj = super(ModelAddForm, self).save()
#         # TODO: move it to model training for new models
#         if self.trainer_obj:
#             obj.set_trainer(self.trainer_obj)
#
#         features_set = FeatureSet.from_model_features_dict(obj.name, obj.features)
#         obj.features_set_id = str(features_set._id)
#         obj.features_set = features_set
#         obj.classifier = PredefinedClassifier.from_model_features_dict(obj.name, obj.features)
#
#         obj.validate()
#         obj.save()
#
#         if obj.status == Model.STATUS_TRAINED:
#             # Processing Model Parameters weights in celery task
#             from api.tasks import fill_model_parameter_weights
#             fill_model_parameter_weights.delay(str(obj._id))
#
#         return obj


class BaseChooseInstanceAndDataset(BaseForm):
    HANDLER_TYPE = 'train'
    TYPE_CHOICES = ('m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge',
                    'hi1.4xlarge', 'hs1.8xlarge')

    fields = ['aws_instance', 'dataset', 'parameters', 'spot_instance_type',
              'format']

    def clean_parameters(self, value):
        self.params_filled = False
        if self.model is None:
            return

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

    def clean_format(self, value):
        if value and value not in DataSet.FORMATS:
            raise ValidationError('Wrong data format')
        return value

    def clean_dataset(self, value):
        if value:
            ds = app.db.DataSet.find_one({'_id': ObjectId(value)})
            if ds is None:
                raise ValidationError('DataSet not found')
            return ds

    def clean_aws_instance(self, value):
        from api.models import Instance
        if value:
            inst = Instance.query.get(value)
            if inst is None:
                raise ValidationError('Instance not found')
            return inst

    def clean_spot_instance_type(self, value):
        if value and value not in self.TYPE_CHOICES:
            raise ValidationError('%s is invalid choice for spot_instance_type. \
Please choose one of %s' % (value, self.TYPE_CHOICES))
        return value

    def validate_obj(self):
        inst_err = only_one_required(
            self.cleaned_data,
            ('spot_instance_type', 'aws_instance'), raise_exc=False)
        ds_err = only_one_required(
            self.cleaned_data,
            ('parameters', 'dataset'), raise_exc=False)
        fmt_err = only_one_required(
            self.cleaned_data,
            ('format', 'dataset'), raise_exc=False)
        if inst_err or ds_err or fmt_err:
            raise ValidationError('%s%s%s.' %
                (inst_err, '. ' if inst_err else '', ds_err))


class BaseChooseInstanceAndDatasetMultiple(BaseChooseInstanceAndDataset):
    def clean_dataset(self, value):
        if value:
            ids = value.split(',')
            ds_list = list(app.db.DataSet.find({'_id': {'$in': [
                ObjectId(ds_id) for ds_id in ids]}}))
            if not ds_list:
                raise ValidationError('DataSet not found')
            return ds_list


class ModelTrainForm(BaseChooseInstanceAndDatasetMultiple):
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
    fields = {
        'name': True,
        'type': True,
        'data': True,
        'import_params': True,
    }

    def clean_type(self, value):
        # if not type in ImportHandler.TYPE_CHOICES:
        #     raise ValidationError('invalid')
        return value


class DataSetAddForm(BaseFormEx):
    required_fields = ('format', 'import_params')
    format = ChoiceField(choices=DataSet.FORMATS)
    import_params = JsonField()

    def before_clean(self):
        self.importhandler = app.db.ImportHandler.get_from_id(
            ObjectId(self.import_handler_id))

    def save(self, commit=True):
        from api.tasks import import_data

        dataset = super(DataSetAddForm, self).save(commit=False)

        str_params = "-".join(["%s=%s" % item
                              for item in dataset.import_params.iteritems()])
        dataset.name = "%s: %s" % (self.importhandler.name, str_params)
        dataset.import_handler_id = str(self.importhandler._id)
        dataset.save(validate=True)
        dataset.set_file_path()
        import_data.delay(str(dataset._id))
        return dataset


class DataSetEditForm(BaseForm):
    fields = ('name',)


# class AddTestForm(BaseChooseInstanceAndDataset):
#     HANDLER_TYPE = 'test'
#     fields = ['name', 'model',
#               'examples_placement',
#               'examples_fields'] + \
#             BaseChooseInstanceAndDataset.fields
#
#     def before_clean(self):
#         self.model = app.db.Model.find_one({'_id': ObjectId(self.model_id)})
#
#     def clean_name(self, value):
#         total = app.db.Test.find({'model_id': self.model_id}).count()
#         return "Test%s" % (total + 1)
#
#     def clean_model(self, value):
#         if self.model is None:
#             raise ValidationError('Model not found')
#
#         if not self.model.example_id:
#             raise ValidationError('Please fill in "Examples id field name"')
#
#         self.cleaned_data['model_name'] = self.model.name
#         self.cleaned_data['model_id'] = self.model_id
#         return self.model
#
#     # def clean_examples_placement(self, value):
#     #     if not value:
#     #         raise ValidationError('Examples placement is required')
#     #
#     #     if value not in app.db.Test.EXAMPLES_STORAGE_CHOICES:
#     #         raise ValidationError('Invalid test examples storage specified')
#     #     return value
#     #
#     # def clean_examples_fields(self, value):
#     #     if not value:
#     #         return []
#     #     return value.split(',')
#
#     def save(self):
#         # placement = self.cleaned_data['examples_placement']
#         # if placement == app.db.Test.EXAMPLES_MONGODB:
#         #     # All fields would be placed to MongoDB
#         #     self.cleaned_data['examples_fields'] = \
#         #         self.model.test_import_handler.get_fields()
#
#         test = BaseForm.save(self, commit=False)
#         test.status = test.STATUS_QUEUED
#         test.examples_placement = app.db.Test.EXAMPLES_MONGODB
#         test.examples_fields = \
#                 self.model.test_import_handler.get_fields()
#         test.save(check_keys=False)
#
#         from api.tasks import run_test, import_data
#         instance = self.cleaned_data.get('aws_instance', None)
#         spot_instance_type = self.cleaned_data.get('spot_instance_type', None)
#
#         if self.params_filled:
#             # load and train
#             from api.models import ImportHandler
#             import_handler = ImportHandler(test.model.test_import_handler)
#             params = self.cleaned_data.get('parameters', None)
#             dataset = import_handler.create_dataset(
#                 params,
#                 data_format=self.cleaned_data.get(
#                     'format', DataSet.FORMAT_JSON)
#             )
#             import_data.apply_async(kwargs={'dataset_id': str(dataset._id),
#                                             'test_id': str(test._id)},
#                                     link=run_test.subtask(args=(str(test._id), ),
#                                     options={'queue': instance['name']}))
#         else:
#             # test using dataset
#             dataset = self.cleaned_data.get('dataset', None)
#             run_test.apply_async(([str(dataset._id),],
#                                   str(test._id),),
#                                   queue=instance['name'])
#             # run_test.run([str(dataset._id),], str(test._id))
#
#         return test


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
                             multi=True)
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
                             multi=True)
        return instance


class FeatureParamsMixin(object):
    """
    Mixin for feature params validation depended on feature type
    """
    def _validate_param(self, data, name):
        from core.trainer.feature_types import FEATURE_PARAMS_TYPES

        if not name in data:
            raise ValidationError('Parameter {} is required'.format(name))
        value = data[name]
        param_type = FEATURE_PARAMS_TYPES[name]['type']

        if not value:
            raise ValidationError('Parameter {} is required'.format(name))

        if param_type == 'str':
            pass  # do nothing

        elif param_type == 'text':
            try:
                json.loads(value)
            except ValueError:
                raise ValidationError('invalid json: {}'.format(value))

        elif param_type == 'dict':
            if not isinstance(value, dict):
                raise ValidationError(
                    '{} should be a dictionary'.format(name))
            if not value.keys():
                raise ValidationError(
                    'Map {} should contain at least one value'.format(name))
            for key, val in value.items():
                if not val:
                    raise ValidationError(
                        'Value {0} in {1} can\'t be empty'.format(key, name))

    def clean_params(self, value, field):
        from core.trainer.feature_types import FEATURE_TYPE_FACTORIES

        value_type = self.data.get('type')
        if not type:
            raise ValidationError('invalid type')
        if not value_type in FEATURE_TYPE_FACTORIES:
            return
        required_params = FEATURE_TYPE_FACTORIES[value_type].required_params
        for name in required_params:
            self._validate_param(value, name)
        return value


class NamedFeatureTypeAddForm(BaseFormEx, FeatureParamsMixin):
    required_fields = ('name', 'type')

    name = CharField()
    type = ChoiceField(choices=app.db.NamedFeatureType.TYPES_LIST)
    input_format = CharField()
    params = JsonField()


class FeatureSetForm(BaseFormEx):
    schema_name = CharField()


class FeatureSetAddForm(BaseForm):
    fields = ('name', 'schema_name', 'classifier', )

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

    def clean_classifier(self, value):
        if not value:
            raise ValidationError('classifier is required')

        classifier = app.db.Classifier.get_from_id(ObjectId(value))
        if not classifier:
            raise ValidationError('classifier not found')

        return classifier


class BasePredefinedForm(BaseFormEx):
    """
    Base form for creating/edditing features specific items, which could be:
        * predefined item - that could be used when creating/edditing
            feature item to copy fields from them
        * feature item like feature transformer, scaler, etc
            when item fields are specified
        * feature item copied from predefined item.
    """
    # name of the feature field of this item or POST/PUT parameter of the
    # predefined item to copy fields from, when `predefined_selected`.
    OBJECT_NAME = None
    DOC = None

    def clean_feature_id(self, value, field):
        if value:
            self.cleaned_data['feature'] = field.doc
        return value

    def clean_model_id(self, value, field):
        if value:
            self.cleaned_data['model'] = field.doc
        return value

    def validate_data(self):
        predefined_selected = self.cleaned_data.get('predefined_selected', False)
        feature_id = self.cleaned_data.get('feature_id', False)
        model_id = self.cleaned_data.get('model_id', False)
        self.cleaned_data['is_predefined'] = is_predefined = \
                not (feature_id or model_id or self.inner_name)

        if predefined_selected and is_predefined:
            raise ValidationError('item could be predefined or copied from predefined')

        if is_predefined:
            name = self.cleaned_data.get('name', None)
            if not name:
                raise ValidationError('name is required for predefined item')
            kwargs = {'name': name}
            if '_id' in self.obj and self.obj._id:
                kwargs['_id'] = {'$ne': self.obj._id}
            callable_document = getattr(app.db, self.DOC)
            count = callable_document.find(kwargs).count()

            if count:
                raise ValidationError('name of predefined item should be unique')

        if predefined_selected:
            obj = self.cleaned_data.get(self.OBJECT_NAME, None)
            if obj:
               self._fill_predefined_values(obj)

    def _fill_predefined_values(self, obj):
        """
        Fills fields from predefined obj
        """
        self.cleaned_data['name'] = obj.name
        self.cleaned_data['type'] = obj.type
        self.cleaned_data['params'] = obj.params

    def save(self, commit=True):
        commit = self.cleaned_data['is_predefined']
        obj = super(BasePredefinedForm, self).save(commit)
        feature = self.cleaned_data.get('feature', None)
        if feature:
            setattr(feature, self.OBJECT_NAME, obj)
            feature.save()

        model = self.cleaned_data.get('model', None)
        if model:
            setattr(model, self.OBJECT_NAME, obj)
            model.save()
        return obj


class ScalerForm(BasePredefinedForm):
    OBJECT_NAME = 'scaler'
    DOC = 'Scaler'

    group_chooser = 'predefined_selected'
    required_fields_groups = {'true': ('scaler', ),
                              'false': ('type', ),
                              None: ('type', )}

    name = CharField()
    type_field = ChoiceField(choices=app.db.Scaler.TYPES_LIST, name='type')
    params = JsonField()
    # whether need to copy feature scaler fields from predefined one
    predefined_selected = BooleanField()
    # whether we need to create predefined item (not feature related)
    scaler = DocumentField(doc='Scaler', by_name=True, return_doc=True)
    feature_id = DocumentField(doc='Feature', by_name=False,
                                return_doc=False)


class ClassifierForm(BasePredefinedForm):
    """
    Form with predefined item selection for model instead of feature
    """
    OBJECT_NAME = 'classifier'
    DOC = 'Classifier'

    group_chooser = 'predefined_selected'
    required_fields_groups = {'true': ('classifier', ),
                              'false': ('type', ),
                              None: ('type', )}

    name = CharField()
    type_field = ChoiceField(choices=app.db.Classifier.TYPES_LIST, name='type')
    params = JsonField()
    # whether need to copy model classifier fields from predefined one
    predefined_selected = BooleanField()
    # whether we need to create predefined item (not model-related)
    classifier = DocumentField(doc='Classifier', by_name=False, return_doc=True)
    model_id = DocumentField(doc='Model', by_name=False, return_doc=False)


class TransformerForm(BasePredefinedForm):
    OBJECT_NAME = 'transformer'
    DOC = 'Transformer'

    group_chooser = 'predefined_selected'
    required_fields_groups = {
        'true': ('transformer', ),
        'false': ('type', ),
        None: ('type', )}

    name = CharField()
    type_field = ChoiceField(choices=app.db.Transformer.TYPES_LIST, name='type')
    params = JsonField()
    predefined_selected = BooleanField()
    transformer = ModelField(model=Transformer, by_name=True, return_model=True)
    feature_id = ModelField(model=Feature, by_name=False,
                                return_model=False)


class FeatureForm(BaseFormEx, FeatureParamsMixin):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'type', 'features_set_id')

    name = CharField()
    type_field = CharField(name='type')
    input_format = CharField()
    params = JsonField()
    required = BooleanField()
    default = CharField()
    is_target_variable = BooleanField()
    features_set_id = ModelField(model=FeatureSet, by_name=False,
                                    return_model=False)

    # TODO:
    # transformer = TransformerForm(model_name='Transformer',
    #                               prefix='transformer-', data_from_request=False)
    remove_transformer = BooleanField()
    # TODO:
    # scaler = ScalerForm(model_name='Scaler', prefix='scaler-',
    #                     data_from_request=False)
    remove_scaler = BooleanField()

    # def clean_features_set_id(self, value, field):        
    #     if value:
    #         feature_set = field.doc
    #         self.cleaned_data['features_set'] = feature_set
    #     return value

    def clean_type(self, value, field):
        if value and not value in app.db.NamedFeatureType.TYPES_LIST:
            # Try to find type in named types
            named_type = app.db.NamedFeatureType.find_one({'name': value})
            if not named_type:
                raise ValidationError('invalid type')
        return value

    def clean_remove_scaler(self, value, field):
        return value and self.is_edit

    def clean_remove_transformer(self, value, field):
        return value and self.is_edit

    def save(self, *args, **kwargs):
        remove_transformer = self.cleaned_data.get('remove_transformer', False)
        if remove_transformer and self.obj.transformer:
            #self.obj.transformer.delete()
            self.obj.transformer = None

        remove_scaler = self.cleaned_data.get('remove_scaler', False)
        if remove_scaler and self.obj.scaler:
            #self.obj.scaler.delete()
            self.obj.scaler = None

        return super(FeatureForm, self).save(*args, **kwargs)


def populate_parser(import_params):
    from flask.ext.restful import reqparse
    parser = reqparse.RequestParser()
    for param in import_params:
        parser.add_argument(param, type=str)
    return parser


def only_one_required(cleaned_data, names, raise_exc=True):
    filled_names = []
    for name in names:
        if cleaned_data.get(name, None):
            filled_names.append(name)
    count = len(filled_names)
    err = None
    if count == 0:
        err = 'One of %s is required' % ', '.join(names)
    elif count > 1:
        err = 'Only one parameter from %s is required. \
%s are filled.' % (', '.join(names), ', '.join(filled_names))

    if err:
        if raise_exc:
            raise ValidationError(err)
        else:
            return err

    return ''
