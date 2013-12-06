from api.decorators import public_actions
from api.import_handlers.models import DataSet
from flask import Response, request
from flask.ext.restful import reqparse
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, undefer, subqueryload, joinedload_all
from werkzeug.datastructures import FileStorage

from api import api
from api.base.resources import BaseResourceSQL, NotFound, ValidationError
from models import Model, Tag, Weight, WeightsCategory
from forms import ModelAddForm, ModelEditForm


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
    PUT_ACTIONS = ('train', 'tags', 'cancel_request_instance')
    FILTER_PARAMS = (('status', str), ('comparable', str), ('tag', str),
                    ('created_by', str), ('updated_by', str))
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
        if not params:
            return cursor
        fields = self._get_show_fields(params)

        get_datasets = False
        get_data_fields = False

        if fields and 'datasets' in fields:
            get_datasets = True
            fields.remove('datasets')
        if fields and 'data_fields' in fields:
            get_data_fields = True
            fields.remove('data_fields')

        if get_datasets or get_data_fields:
            cursor = cursor.options(joinedload_all(Model.datasets))

        if fields and 'features' in fields:
            fields.append('features_set_id')
            cursor = cursor.options(joinedload(Model.features_set))
            cursor = cursor.options(undefer(Model.classifier))

        if fields and 'test_handler_fields' in fields:
            cursor = cursor.options(joinedload(Model.test_import_handler))

        return cursor

    def _get_by_importhandler_action(self, **kwargs):
        parser_params = self.GET_PARAMS + (('handler', str), )
        params = self._parse_parameters(parser_params)
        handler_id = params.get('handler')
        models = Model.filter(or_(
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
            content = model.get_trainer(loaded=False)
        else:
            content = model.get_features_json()

        filename = "%s-%s.%s" % (model.name, field,
                                 'dat' if field == 'trainer' else 'json')

        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
        return resp

    # POST/PUT specific methods
    def _put_train_action(self, **kwargs):
        from api.tasks import train_model, import_data, \
            request_spot_instance, get_request_instance
        from api.forms import ModelTrainForm
        from celery import chain
        obj = self._get_details_query(None, **kwargs)
        form = ModelTrainForm(obj=obj, **kwargs)
        if form.is_valid():
            model = form.save()
            instance = form.cleaned_data.get('aws_instance', None)
            spot_instance_type = form.cleaned_data.get('spot_instance_type', None)

            tasks_list = []
            # Removing old log messages
            # TODO
            # app.db.LogMessage.collection.remove({'type': 'trainmodel_log',
            #                                     'params.obj': model._id})
            if form.params_filled:
                from api.models import ImportHandler
                import_handler = ImportHandler(model.train_import_handler)
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

            if not spot_instance_type is None:
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
                        'interval_max': 10
                        }))
            elif not instance is None:
                if form.params_filled:
                    train_model_args = (model.id, request.user.id)
                else:
                    train_model_args = (dataset_ids, model.id, request.user.id)
                tasks_list.append(train_model.subtask(train_model_args, {},
                                                      queue=instance.name))
            chain(tasks_list).apply_async()
            return self._render({
                self.OBJECT_NAME: model
            })

    def _put_cancel_request_instance_action(self, **kwargs):
        from api.tasks import cancel_request_spot_instance
        model = self._get_details_query(None, **kwargs)
        request_id = model.get('spot_instance_request_id')
        if request_id and model.status == model.STATUS_REQUESTING_INSTANCE:
            cancel_request_spot_instance.delay(request_id, model.id)
            model.status = model.STATUS_CANCELED
        return self._render({
            self.OBJECT_NAME: model
        })

api.add_resource(ModelResource, '/cloudml/models/')


class TagResource(BaseResourceSQL):
    """
    Tags API methods
    """
    MESSAGE404 = "Tag doesn't exist"
    OBJECT_NAME = 'tag'
    DEFAULT_FIELDS = [u'_id']
    Model = Tag

api.add_resource(TagResource, '/cloudml/tags/')
