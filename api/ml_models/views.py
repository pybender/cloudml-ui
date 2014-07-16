from api.logs.mongo.models import LogMessage
from flask import Response, request
from flask.ext.restful import reqparse
from sqlalchemy import or_
from sqlalchemy.orm import undefer, joinedload_all
from werkzeug.datastructures import FileStorage

from api import api
from api.base.models import db
from api.import_handlers.models import DataSet
from api.base.resources import BaseResourceSQL, NotFound, ValidationError, \
    public_actions, ERR_INVALID_DATA, odesk_error_response
from models import Model, Tag, Weight, WeightsCategory, Segment
from forms import ModelAddForm, ModelEditForm
from api.servers.forms import ChooseServerForm


model_parser = reqparse.RequestParser()
model_parser.add_argument('importhandler', type=str,
                          default=None)
model_parser.add_argument('train_importhandler', type=str)
model_parser.add_argument('features', type=str)
model_parser.add_argument('trainer', type=FileStorage, location='files')
model_parser.add_argument('name', type=str, default=None)
model_parser.add_argument('example_id', type=str, default=None)
model_parser.add_argument('example_label', type=str, default=None)

class ModelResource(BaseResourceSQL):
    """
    Models API methods
    """
    GET_ACTIONS = ('download', 'reload', 'by_importhandler')
    PUT_ACTIONS = ('train', 'tags', 'cancel_request_instance',
                   'upload_to_server')
    FILTER_PARAMS = (('status', str), ('comparable', str), ('tag', str),
                    ('created_by', str), ('updated_by_id', int),
                    ('updated_by', str), ('name', str))
    DEFAULT_FIELDS = ('id', 'name')
    NEED_PAGING = True

    MESSAGE404 = "Model with name %(_id)s doesn't exist"

    post_form = ModelAddForm
    put_form = ModelEditForm

    DOWNLOAD_FIELDS = ('trainer', 'features')

    Model = Model

    def _get_model_parser(self, **kwargs):
        """
        Returns Model parser that used when POST model.
        """
        return model_parser

    # GET specific methods

    @public_actions(['download'])
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

        # if fields and 'test_handler_fields' in fields:
        #     cursor = cursor.options(joinedload_all(Model.test_import_handler))

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

    def _get_download_action(self, **kwargs):
        """
        Downloads trained model, importhandler or features
        (specified in GET param `field`) file.
        """
        model = self._get_details_query(None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        params = self._parse_parameters((('field', str), ))
        field = params.get('field', 'trainer')

        if not field in self.DOWNLOAD_FIELDS:
            raise ValidationError('Invalid field specified. \
Valid values are %s' % ','.join(self.DOWNLOAD_FIELDS))

        if field == 'trainer':
            content = model.get_trainer(loaded=False).encode('zlib')
        else:
            content = model.get_features_json()

        filename = "%s-%s.%s" % (model.name, field,
                                 'dat.gz' if field == 'trainer' else 'json')

        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = \
            'attachment; filename=%s' % filename
        return resp

    # POST/PUT specific methods
    def _put_train_action(self, **kwargs):
        from tasks import train_model
        from api.import_handlers.tasks import import_data
        from api.instances.tasks import request_spot_instance, \
            get_request_instance
        from forms import ModelTrainForm
        from celery import chain
        obj = self._get_details_query(None, **kwargs)
        form = ModelTrainForm(obj=obj, **kwargs)
        if form.is_valid():
            model = form.save()  # set status to queued
            new_dataset_selected = form.cleaned_data.get('new_dataset_selected')
            existing_instance_selected = form.cleaned_data.get('existing_instance_selected')
            instance = form.cleaned_data.get('aws_instance', None)
            spot_instance_type = form.cleaned_data.get(
                'spot_instance_type', None)

            tasks_list = []
            LogMessage.delete_related_logs(model)
            if new_dataset_selected:
                import_handler = model.train_import_handler
                params = form.cleaned_data.get('parameters', None)
                dataset = import_handler.create_dataset(
                    params,
                    data_format=form.cleaned_data.get(
                        'format', DataSet.FORMAT_JSON)
                )
                tasks_list.append(import_data.s(dataset.id, model.id))
                dataset = [dataset]
            else:
                dataset = form.cleaned_data.get('dataset', None)
            dataset_ids = [ds.id for ds in dataset]

            if not existing_instance_selected:  # request spot instance
                tasks_list.append(request_spot_instance.s(
                    instance_type=spot_instance_type,
                    model_id=model.id
                ))
                tasks_list.append(get_request_instance.subtask(
                    (),
                    {
                        'callback': 'train',
                        'dataset_ids': dataset_ids,
                        'model_id': model.id,
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
                if new_dataset_selected:
                    train_model_args = (model.id, request.user.id)
                else:
                    train_model_args = (dataset_ids, model.id, request.user.id)
                tasks_list.append(train_model.subtask(train_model_args, {},
                                                      queue=instance.name))
            chain(tasks_list).apply_async()
            return self._render({
                self.OBJECT_NAME: {
                    'id': model.id
                }
            })

    def _put_cancel_request_instance_action(self, **kwargs):
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

    def _put_upload_to_server_action(self, **kwargs):
        from api.servers.tasks import upload_model_to_server

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

api.add_resource(ModelResource, '/cloudml/models/')


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
            direction = Weight.value.desc() if is_positive else Weight.value.asc()
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
    FILTER_PARAMS = (('parent', str), ('segment', str))
    ALLOWED_METHODS = ('get', )

    def _list(self, **kwargs):
        params = self._parse_parameters(self.FILTER_PARAMS)
        model_id = kwargs.get('model_id')
        kwargs['parent'] = params.get('parent') or ''
        segment = get_segment(model_id, params.get('segment'))
        kwargs['segment_id'] = segment.id if segment else None

        opts = self._prepare_show_fields_opts(
            WeightsCategory, ('short_name', 'name'))
        categories = WeightsCategory.query.options(
            *opts).filter_by(**kwargs)

        class_label, class_query = get_class_label(model_id, params)
        if class_query:
            kwargs['class_label'] = class_label

        opts = self._prepare_show_fields_opts(
            Weight, ('short_name', 'name', 'css_class', 'value', 'segment_id'))
        weights = Weight.query.options(*opts).filter_by(**kwargs)
        context = {'categories': categories, 'weights': weights}
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
    multiclass). `class_query`, a boolean flag to include the class_label retuned
    when queyring for weights (true) or not (false)
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
