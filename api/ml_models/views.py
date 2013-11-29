from api.decorators import public_actions
from bson import ObjectId
from flask import Response, request
from flask.ext.restful import reqparse
from werkzeug.datastructures import FileStorage

from api import api
from api.resources import BaseResourceSQL, NotFound, ValidationError
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
    FILTER_PARAMS = (('status', str), ('comparable', int), ('tag', str),
                    ('created_by', str), ('updated_by', str))
    DEFAULT_FIELDS = ('_id', 'name')
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

    def _get_details_query(self, params, fields, **kwargs):
        get_datasets = False
        get_data_fields = False
        if fields and 'datasets' in fields:
            get_datasets = True
            fields.remove('datasets')
        if fields and 'data_fields' in fields:
            get_data_fields = True
            fields.remove('data_fields')

        if get_datasets or get_data_fields:
            fields.append('dataset_ids')

        if fields and 'features' in fields:
            fields.append('features_set')
            fields.append('features_set_id')
            fields.append('classifier')

        if fields and 'test_handler_fields' in fields:
            fields.append('test_import_handler')

        model = super(ModelResource, self)._get_details_query(
            params, fields, **kwargs)

        if get_datasets:
            model['datasets'] = [{
                '_id': str(ds._id),
                'name': ds.name,
                'import_handler_id': str(ds.import_handler_id),
            } for ds in model.datasets_list]

        if get_data_fields:
            model['data_fields'] = model.dataset.data_fields\
                if model.dataset else []

        if fields and 'test_handler_fields' in fields:
            if model.test_import_handler:
                model['test_handler_fields'] = model.test_import_handler.get_fields()

        if fields and 'features' in fields:
            model['features'] = model.get_features_json()

        return model

    # TODO
    # def _prepare_filter_params(self, params):
    #     pdict = super(ModelResource, self)._prepare_filter_params(params)
    #     if 'comparable' in pdict:
    #         pdict['comparable'] = bool(pdict['comparable'])
    #     if 'tag' in pdict:
    #         pdict['tags'] = {'$in': [pdict['tag']]}
    #         del pdict['tag']
    #     if 'created_by' in pdict:
    #         pdict['created_by.uid'] = pdict['created_by']
    #         del pdict['created_by']
    #     if 'updated_by' in pdict:
    #         pdict['updated_by.uid'] = pdict['updated_by']
    #         del pdict['updated_by']
    #     return pdict

    def _get_by_importhandler_action(self, **kwargs):
        parser_params = self.GET_PARAMS + (('handler', str), )
        params = self._parse_parameters(parser_params)
        query_fields, show_fields = self._get_fields(params)
        _id = ObjectId(params.get('handler'))
        expr = {'$or': [{'test_import_handler.$id': _id},
                        {'train_import_handler.$id': _id}]}
        models = self.Model.find(expr, query_fields)
        return self._render({"%ss" % self.OBJECT_NAME: models})

    def _get_download_action(self, **kwargs):
        """
        Downloads trained model, importhandler or features
        (specified in GET param `field`) file.
        """
        model = self._get_details_query(None, None, **kwargs)
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
            request_spot_instance, self_terminate, get_request_instance
        from api.tasks import cancel_request_spot_instance
        from api.forms import ModelTrainForm
        from celery import chain
        obj = self._get_details_query(None, None, **kwargs)
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
                tasks_list.append(import_data.s(str(dataset._id),
                                                str(model._id)))
                dataset = [dataset]
            else:
                dataset = form.cleaned_data.get('dataset', None)

            dataset_ids = [str(ds._id) for ds in dataset]

            if not spot_instance_type is None:
                tasks_list.append(request_spot_instance.s(instance_type=spot_instance_type,
                                                          model_id=str(model._id)))
                tasks_list.append(get_request_instance.subtask(
                    (),
                    {
                        'callback': 'train',
                        'dataset_ids': dataset_ids,
                        'model_id': str(model._id),
                        'user_id': str(request.user.id),
                    },
                    retry=True,
                    countdown=10,
                    retry_policy={
                        'max_retries': 3,
                        'interval_start': 5,
                        'interval_step': 5,
                        'interval_max': 10
                        }))
                #tasks_list.append(self_terminate.s())
            elif not instance is None:
                if form.params_filled:
                    train_model_args = (str(model._id), request.user.id)
                else:
                    train_model_args = (dataset_ids, str(model._id),
                                        request.user.id)
                tasks_list.append(train_model.subtask(train_model_args, {},
                                                      queue=instance.name))
            chain(tasks_list).apply_async()
            return self._render(self._get_save_response_context(model, extra_fields=['status']))

    def _put_cancel_request_instance_action(self, **kwargs):
        from api.tasks import cancel_request_spot_instance
        model = self._get_details_query(None, None, **kwargs)
        request_id = model.get('spot_instance_request_id')
        if request_id and model.status == model.STATUS_REQUESTING_INSTANCE:
            cancel_request_spot_instance.delay(request_id, str(model._id))
            model.status = model.STATUS_CANCELED
        return self._render(self._get_save_response_context(model, extra_fields=['status']))

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
