"""
Model, Transformer, Segments, Weights-related REST API declared here.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json

from flask import Response, request
from flask.ext.restful import reqparse
from sqlalchemy import or_, func
from sqlalchemy.orm import undefer, joinedload_all
from werkzeug.datastructures import FileStorage

from api import app, api
from api.async_tasks.models import AsyncTask
from api.features.models import Feature, FeatureSet
from api.import_handlers.models import DataSet
from api.base.resources import BaseResourceSQL, NotFound, ValidationError, \
    public_actions, ERR_INVALID_DATA, odesk_error_response, _select
from api.base.resources.utils import ERR_INVALID_METHOD
from models import Model, Tag, Weight, WeightsCategory, Segment, Transformer, \
    ClassifierGridParams
from forms import ModelAddForm, ModelEditForm, TransformDataSetForm, \
    TrainForm, TransformerForm, FeatureTransformerForm, GridSearchForm, \
    VisualizationOptionsForm


model_parser = reqparse.RequestParser()
model_parser.add_argument('importhandler', type=str,
                          default=None)
model_parser.add_argument('train_importhandler', type=str)
model_parser.add_argument('features', type=str)
model_parser.add_argument('trainer', type=FileStorage, location='files')
model_parser.add_argument('name', type=str, default=None)
model_parser.add_argument('example_id', type=str, default=None)
model_parser.add_argument('example_label', type=str, default=None)


class BaseTrainedEntityResource(BaseResourceSQL):
    PUT_ACTIONS = ['train']
    GET_ACTIONS = ['trainer_download_s3url']
    DEFAULT_FIELDS = ('id', 'name')
    ENTITY_TYPE = 'model'

    @property
    def train_entity_task(self):
        raise NotImplemented()

    @property
    def train_form(self):
        raise NotImplemented()

    def _get_trainer_download_s3url_action(self, **kwargs):
        entity = self._get_details_query(None, **kwargs)
        if entity is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        url = entity.get_trainer_s3url()
        return self._render({'trainer_file_for': entity.id, 'url': url})

    def _put_train_action(self, **kwargs):
        from api.import_handlers.tasks import import_data
        from api.instances.tasks import request_spot_instance, \
            get_request_instance
        from celery import chain
        obj = self._get_details_query(None, **kwargs)
        if not app.config['MODIFY_DEPLOYED_MODEL'] and \
           self.ENTITY_TYPE == 'model' and obj.locked:
            return odesk_error_response(405, ERR_INVALID_METHOD,
                                        'Re-train is forbidden. Model is '
                                        'deployed and blocked for '
                                        'modifications.')

        delete_metadata = obj.status != obj.STATUS_NEW
        form = self.train_form(obj=obj, **kwargs)
        if form.is_valid():
            entity = form.save()  # set status to queued
            entity_key = '{0}_id'.format(self.ENTITY_TYPE)
            new_dataset_selected = form.cleaned_data.get(
                'new_dataset_selected')
            existing_instance_selected = form.cleaned_data.get(
                'existing_instance_selected')
            instance = form.cleaned_data.get('aws_instance', None)
            spot_instance_type = form.cleaned_data.get(
                'spot_instance_type', None)

            tasks_list = []
            if new_dataset_selected:
                import_handler = entity.train_import_handler
                params = form.cleaned_data.get('parameters', None)
                dataset = import_handler.create_dataset(
                    params,
                    data_format=form.cleaned_data.get(
                        'format', DataSet.FORMAT_JSON)
                )
                opts = {
                    'dataset_id': dataset.id,
                    entity_key: entity.id
                }
                tasks_list.append(import_data.s(**opts))
                dataset = [dataset]
            else:
                dataset = form.cleaned_data.get('dataset', None)
            dataset_ids = [ds.id for ds in dataset]

            if not existing_instance_selected:  # request spot instance
                if self.ENTITY_TYPE != 'model':
                    raise NotImplemented()

                tasks_list.append(request_spot_instance.s(
                    instance_type=spot_instance_type,
                    model_id=entity.id
                ))
                tasks_list.append(get_request_instance.subtask(
                    (),
                    {
                        'callback': 'train',
                        'dataset_ids': dataset_ids,
                        'model_id': entity.id,
                        'user_id': request.user.id,
                    },
                    retry=True,
                    countdown=10,
                    retry_policy={
                        'max_retries': 3,
                        'interval_start': 5,
                        'interval_step': 5,
                        'interval_max': 10}))
            else:
                opts = {
                    entity_key: entity.id,
                    'user_id': request.user.id,
                    'delete_metadata': delete_metadata
                }
                if not new_dataset_selected:
                    opts['dataset_ids'] = dataset_ids
                tasks_list.append(self.train_entity_task.subtask(
                    None, opts, queue=instance.name))

            chain(tasks_list).apply_async()
            return self._render({
                self.OBJECT_NAME: {
                    'id': entity.id,
                    'status': entity.status,
                    'training_in_progress': entity.training_in_progress
                }
            })

    def _put_cancel_request_instance_action(self, **kwargs):
        if self.ENTITY_TYPE != 'model':
            raise NotImplemented()
        from api.instances.tasks import cancel_request_spot_instance
        model = self._get_details_query(None, **kwargs)
        request_id = model.spot_instance_request_id
        if request_id and model.status == model.STATUS_REQUESTING_INSTANCE:
            cancel_request_spot_instance.delay(request_id, model.id)
            model.status = model.STATUS_CANCELED
        return self._render({
            self.OBJECT_NAME: {
                'id': model.id,
                'status': model.status
            }
        })


class ModelResource(BaseTrainedEntityResource):
    """
    Models API methods
    """
    GET_ACTIONS = ('reload', 'by_importhandler', 'trainer_download_s3url',
                   'features_download', 'dataset_download', 'weights_download')
    PUT_ACTIONS = ('train', 'tags', 'cancel_request_instance',
                   'upload_to_server', 'dataset_download', 'grid_search',
                   'import_features_from_xml_ih', 'generate_visualization')
    POST_ACTIONS = ('clone', )
    FILTER_PARAMS = (('status', str), ('comparable', str), ('tag', str),
                     ('created_by', str), ('updated_by_id', int),
                     ('updated_by', str), ('name', str))
    NEED_PAGING = True

    MESSAGE404 = "Model with name %(_id)s doesn't exist"

    post_form = ModelAddForm
    put_form = ModelEditForm
    train_form = TrainForm

    Model = Model

    @property
    def train_entity_task(self):
        from tasks import train_model
        return train_model

    def _get_model_parser(self, **kwargs):
        """
        Returns Model parser that used when POST model.
        """
        return model_parser

    # GET specific methods

    @public_actions(['features_download', 'weights_download'])
    def get(self, *args, **kwargs):
        return super(ModelResource, self).get(*args, **kwargs)

    def _modify_details_query(self, cursor, params):
        fields = self._get_show_fields(params)
        if not fields:
            return cursor

        if fields and 'data_fields' in fields:
            cursor = cursor.options(joinedload_all(Model.datasets))

        if fields and 'features' in fields:
            cursor = cursor.options(joinedload_all(Model.features_set))
            cursor = cursor.options(undefer(Model.classifier))

        return cursor

    def _set_list_query_opts(self, cursor, params):
        if 'tag' in params and params['tag']:
            cursor = cursor.filter(Model.tags.any(Tag.text == params['tag']))
        name = params.pop('name', None)
        if name:
            cursor = cursor.filter(Model.name.ilike('%{0}%'.format(name)))
        created_by = params.pop('created_by', None)
        if created_by:
            cursor = cursor.filter(Model.created_by.has(uid=created_by))
        updated_by = params.pop('updated_by', None)
        if updated_by:
            cursor = cursor.filter(Model.updated_by.has(uid=updated_by))

        return cursor

    def _get_by_importhandler_action(self, **kwargs):
        parser_params = self.GET_PARAMS + (('handler', str), )
        params = self._parse_parameters(parser_params)
        handler_id = params.get('handler')
        models = Model.query.filter(or_(
            Model.train_import_handler_id == handler_id,
            Model.test_import_handler_id == handler_id,
        )).all()
        return self._render({"%ss" % self.OBJECT_NAME: models})

    def _get_features_download_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        content = model.get_features_json()
        resp = Response(content)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Content-Disposition'] = \
            'attachment; filename=%s-features.json' % model.name
        return resp

    def _get_weights_download_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        if model.status != model.STATUS_TRAINED:
            raise ValidationError('Model should be trained')
        if not model.weights_synchronized:
            raise ValidationError('Model weights should be synchronized')

        trainer = model.get_trainer(force_load=True)
        result = {}
        for segment in model.segments:
            result[segment.name] = trainer.get_weights(segment.name)
        content = json.dumps(result)

        resp = Response(content)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Content-Disposition'] = \
            'attachment; filename=%s-weights.json' % model.name
        return resp

        # with open(args.weights, 'w') as weights_fp:
        #     trainer.store_feature_weights(weights_fp)

    def _put_grid_search_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)

        form = GridSearchForm(model=model, Model=ClassifierGridParams)
        if form.is_valid():
            from tasks import get_classifier_parameters_grid
            params_grid = form.save()
            get_classifier_parameters_grid.delay(params_grid.id)
            return self._render({
                self.OBJECT_NAME: model
            })

    def _put_generate_visualization_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)
        if not app.config['MODIFY_DEPLOYED_MODEL'] and model.locked:
            return odesk_error_response(405, ERR_INVALID_METHOD,
                                        'Forbidden to change visualization '
                                        'data. Model is deployed and blocked '
                                        'for modifications.')

        form = VisualizationOptionsForm(obj=model)
        if form.is_valid():
            form.process()
            return self._render({
                self.OBJECT_NAME: model
            })

    def _post_clone_action(self, **kwargs):
        from datetime import datetime
        model = self._get_details_query(None, **kwargs)
        name = "{0} clone: {1}".format(
            model.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        new_model = Model(
            name=name,
            train_import_handler=model.train_import_handler,
            test_import_handler=model.test_import_handler
        )
        new_model.save()
        new_model.classifier = model.classifier
        new_model.features_set.from_dict(
            model.features_set.features, commit=False)
        new_model.tags = model.tags
        new_model.save()
        return self._render({
            self.OBJECT_NAME: new_model,
            'status': 'New model "{0}" created'.format(
                new_model.name
            )
        }, code=201)

    def _put_upload_to_server_action(self, **kwargs):
        from api.servers.tasks import upload_model_to_server
        from api.servers.forms import ChooseServerForm

        model = self._get_details_query(None, **kwargs)
        if model.status != Model.STATUS_TRAINED:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Model is not yet trained')

        form = ChooseServerForm(obj=model)
        if form.is_valid():
            server = form.cleaned_data['server']
            upload_model_to_server.delay(server.id, model.id,
                                         request.user.id)

            return self._render({
                self.OBJECT_NAME: model,
                'status': 'Model "{0}" will be uploaded to server'.format(
                    model.name
                )
            })

    def _put_dataset_download_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)
        if model is None:
            raise NotFound('Model not found')
        if model.status != Model.STATUS_TRAINED:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Model is not trained')

        form = TransformDataSetForm(obj=model)
        if not form.is_valid():
            return

        dataset = form.cleaned_data['dataset']

        from api.ml_models.tasks import transform_dataset_for_download
        transform_dataset_for_download.delay(model.id, dataset.id)
        return self._render({})

    def _get_dataset_download_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)
        if model is None:
            raise NotFound('Model not found')

        from api.tasks import TRANSFORM_DATASET_TASK
        tasks = AsyncTask.get_current_by_object(
            model, TRANSFORM_DATASET_TASK)

        downloads = []
        for task in tasks:
            downloads.append({
                'dataset': DataSet.query.get(task.args[1]),
                'task': task
            })

        return self._render({self.OBJECT_NAME: model.id,
                             'downloads': downloads})

    def _put_import_features_from_xml_ih_action(self, **kwargs):
        model = self._get_details_query(None, **kwargs)
        error_response = odesk_error_response(
            405, ERR_INVALID_METHOD,
            'Only new models with 0 features and Xml import handler as '
            'trainer is allowed for this feature')

        if model.status != Model.STATUS_NEW:
            return error_response

        if model.train_import_handler_type.lower() != 'xml':
            return error_response

        features_count = Feature.query.join(
            FeatureSet, FeatureSet.id == Feature.feature_set_id).join(
                Model, Model.features_set_id == FeatureSet.id).filter(
                    Model.id == model.id).with_entities(
                        func.count(Feature.id)).scalar()

        if features_count > 0:
            return error_response

        fields = model.train_import_handler.list_fields()
        features = []
        for field in fields:
            feature = Feature()
            feature.name = field.name
            feature.type = Feature.field_type_to_feature_type(field.type)
            feature.feature_set_id = model.features_set_id
            feature.save(commit=False)
            features.append(feature)
        app.sql_db.session.commit()
        return self._render({self.OBJECT_NAME: model.id,
                             'features': [f.to_dict() for f in features]})


api.add_resource(ModelResource, '/cloudml/models/')


class TransformerResource(BaseTrainedEntityResource):
    """ Pretrained transformer API methods """
    Model = Transformer
    GET_ACTIONS = BaseTrainedEntityResource.GET_ACTIONS + ['configuration']
    ENTITY_TYPE = 'transformer'
    DEFAULT_FIELDS = ['name', 'type', 'params']
    FILTER_PARAMS = (('status', str), )
    put_form = TransformerForm
    train_form = TrainForm
    NEED_PAGING = False

    @property
    def post_form(self):
        from flask import request
        feature_id = request.form.get("feature_id", None)
        if feature_id is not None:
            return FeatureTransformerForm

        return TransformerForm  # adds pretrained transformer

    @property
    def train_entity_task(self):
        from tasks import train_transformer
        return train_transformer

    def _get_configuration_action(self, **kwargs):
        from api.features.config import TRANSFORMERS
        return self._render({'configuration': TRANSFORMERS})

api.add_resource(TransformerResource, '/cloudml/transformers/')


class TagResource(BaseResourceSQL):
    """ Tags API methods """
    DEFAULT_FIELDS = [u'_id']
    Model = Tag

api.add_resource(TagResource, '/cloudml/tags/')


class WeightResource(BaseResourceSQL):
    """ Model Parameters weights API methods """
    ALLOWED_METHODS = ('get', )
    GET_ACTIONS = ('brief', )
    NEED_PAGING = True
    FILTER_PARAMS = (('is_positive', int), ('q', str), ('parent', str),
                     ('segment', str), ('segment_id', str),
                     ('class_label', str))

    Model = Weight

    def _prepare_filter_params(self, params):
        pdict = super(WeightResource, self)._prepare_filter_params(params)
        if 'is_positive' in pdict:
            if pdict['is_positive'] == 1:
                pdict['is_positive'] = True
            elif pdict['is_positive'] == -1:
                pdict['is_positive'] = False
            else:
                del pdict['is_positive']
        return pdict

    def _set_list_query_opts(self, cursor, params):
        if 'q' in params and params['q']:

            # Full text search
            query = '{0} | {0}:*'.format(params['q'])
            query_like = '%{0}%'.format(params['q'])
            cursor = cursor.filter(
                "(fts @@ to_tsquery(:q) OR weight.name LIKE :q_like)"
            ).params(q=query, q_like=query_like)

        return cursor

    def _get_brief_action(self, per_page=50, **kwargs):
        """ Gets list with Model's weighted parameters with pagination. """
        model_id = kwargs.get('model_id')
        paging_params = (('ppage', int), ('npage', int),)
        params = self._parse_parameters(
            self.GET_PARAMS + paging_params + self.FILTER_PARAMS)

        # Paginate weights
        ppage = params.get('ppage') or 1
        npage = params.get('npage') or 1
        segment = get_segment(model_id, params.get('segment'))
        segment_id = segment.id if segment else None
        class_label, class_query = get_class_label(model_id, params)

        def get_weights(is_positive):
            qry = self.Model.query.filter(Weight.model_id == model_id,
                                          Weight.is_positive == is_positive)
            if segment_id is not None:
                qry = qry.filter(Weight.segment_id == segment_id)
            if class_query is True:
                qry = qry.filter(Weight.class_label == class_label)

            page = ppage if is_positive else npage
            direction = Weight.value.desc() if is_positive \
                else Weight.value.asc()
            return qry.order_by(direction).offset((page - 1) * per_page)\
                .limit(per_page)

        context = {'positive_weights': get_weights(True),
                   'negative_weights': get_weights(False),
                   'class_label': class_label}
        return self._render(context)

api.add_resource(WeightResource, '/cloudml/weights/\
<regex("[\w\.]*"):model_id>/')


class WeightTreeResource(BaseResourceSQL):
    """
    Model Parameters weights categories/weights API methods

    NOTE: it used for constructing tree of model parameters.
    """
    FILTER_PARAMS = (('parent', str), ('segment', str),
                     ('test_id', int), ('class_label', str))
    ALLOWED_METHODS = ('get', )

    def _list(self, **kwargs):
        params = self._parse_parameters(self.FILTER_PARAMS)
        model_id = kwargs.get('model_id')
        kwargs['parent'] = params.get('parent') or ''
        segment = get_segment(model_id, params.get('segment'))
        kwargs['segment_id'] = segment.id if segment else None

        class_label, class_query = get_class_label(model_id, params)
        if class_query:
            kwargs['class_label'] = class_label

        opts = self._prepare_show_fields_opts(
            WeightsCategory, ('short_name', 'name', 'normalized_weight'))
        categories = WeightsCategory.query.options(
            *opts).filter_by(**kwargs)

        extra_fields = {}
        field_names = ['short_name', 'name', 'css_class',
                       'value', 'segment_id', 'value2']
        if params['test_id']:
            test_weight = Weight.test_weight(str(params['test_id']))
            extra_fields = {'test_weight': test_weight}

        context = {
            'categories': categories,
            'weights': _select(Weight, field_names, kwargs, extra_fields)}
        return self._render(context)

api.add_resource(WeightTreeResource,
                 '/cloudml/weights_tree/<regex("[\w\.]*"):model_id>/',
                 add_standard_urls=False)


def get_segment(model_id, name=None):
    if name is None:
        return Segment.query.filter_by(model_id=model_id).first()
    else:
        return Segment.query.filter_by(model_id=model_id, name=name).one()


def get_class_label(model_id, params):
    """
    Default behavior for getting class_label for weights querying.
    :param model_id:
    :param params: params parsed from query string
    :return: tuple (class_label, class_query), `class_label` the class label
    based on the passed QS parameters if any, the type of model (binary,
    multiclass). `class_query`, a boolean flag to include the class_label
    retuned when queyring for weights (true) or not (false)
    """
    ml_model = Model.query.get(model_id)

    if ml_model.labels is None or len(ml_model.labels) == 0:
        # take care of edge case, of old models without labels field
        class_label = '1'
        class_query = False
    elif len(ml_model.labels) == 2:
        # binary classifer
        class_label = '1'
        class_query = False
    else:
        # multiclass
        class_label = params.get('class_label') or ml_model.labels[0]
        class_query = True

    return class_label, class_query
