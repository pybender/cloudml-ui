from datetime import datetime
import json
import logging
import traceback
from api.models import TestExampleSql
from flask.ext.restful import reqparse
from flask import request, Response

import gevent
from pymongo.errors import OperationFailure
from werkzeug.datastructures import FileStorage
from bson.objectid import ObjectId

from api import api, app
from api.decorators import public, public_actions
from api.utils import ERR_INVALID_DATA, odesk_error_response, \
    ERR_NO_SUCH_MODEL, ERR_UNPICKLING_MODEL
from api.resources import BaseResource, NotFound, ValidationError, BaseResourceSQL
from api.forms import *
from core.importhandler.importhandler import ExtractionPlan, \
    RequestImportHandler

model_parser = reqparse.RequestParser()
model_parser.add_argument('importhandler', type=str,
                          default=None)
model_parser.add_argument('train_importhandler', type=str)
model_parser.add_argument('features', type=str)
model_parser.add_argument('trainer', type=FileStorage, location='files')
model_parser.add_argument('name', type=str, default=None)
model_parser.add_argument('example_id', type=str, default=None)
model_parser.add_argument('example_label', type=str, default=None)


def event_stream(query_params={}):  # pragma: no cover
    curs = app.chan.cursor(query_params, False)
    while True:
        gevent.sleep(0.2)
        try:
            msg = curs.next()
            if msg:
                yield 'data: %s\n\n' % json.dumps(msg)
        except StopIteration:
            continue
        except OperationFailure, err:
            logging.error("op", err)
            break


@app.route('/cloudml/log/')
def sse_request():  # pragma: no cover
    query_params = {}
    channel = request.args.get('channel')
    if channel:
        if channel not in app.PUBSUB_CHANNELS.keys():
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Invalid channel name')
        query_params['k'] = channel

        params = app.PUBSUB_CHANNELS[channel]
        for name in params:
            val = request.args.get(name)
            if val:
                query_params["data.%s" % name] = val

    resp = Response(event_stream(query_params),
                    mimetype='text/event-stream')
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


class Models(BaseResource):
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

    @property
    def Model(self):
        return app.db.Model

    def _get_model_parser(self, **kwargs):
        """
        Returns Model parser that used when POST model.
        """
        return model_parser

    # GET specific methods

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(Models, self).get(*args, **kwargs)

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

        model = super(Models, self)._get_details_query(
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

    def _prepare_filter_params(self, params):
        pdict = super(Models, self)._prepare_filter_params(params)
        if 'comparable' in pdict:
            pdict['comparable'] = bool(pdict['comparable'])
        if 'tag' in pdict:
            pdict['tags'] = {'$in': [pdict['tag']]}
            del pdict['tag']
        if 'created_by' in pdict:
            pdict['created_by.uid'] = pdict['created_by']
            del pdict['created_by']
        if 'updated_by' in pdict:
            pdict['updated_by.uid'] = pdict['updated_by']
            del pdict['updated_by']
        return pdict

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
            app.db.LogMessage.collection.remove({'type': 'trainmodel_log',
                                                'params.obj': model._id})
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
                        'user_id': str(request.user._id),
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
                    train_model_args = (str(model._id), str(request.user._id))
                else:
                    train_model_args = (dataset_ids, str(model._id),
                                        str(request.user._id))
                tasks_list.append(train_model.subtask(train_model_args, {},
                                                      queue=instance['name']))
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

api.add_resource(Models, '/cloudml/models/')


class WeightsResource(BaseResource):
    """
    Model Parameters weights API methods
    """
    GET_ACTIONS = ('brief', )
    ENABLE_FULLTEXT_SEARCH = True
    OBJECT_NAME = 'weight'
    NEED_PAGING = True
    FILTER_PARAMS = (('is_positive', int), ('q', str), ('parent', str), )

    @property
    def Model(self):
        return app.db.Weight

    def _prepare_filter_params(self, params):
        pdict = super(WeightsResource, self)._prepare_filter_params(params)
        if 'is_positive' in pdict:
            if pdict['is_positive'] == 1:
                pdict['is_positive'] = True
            elif pdict['is_positive'] == -1:
                pdict['is_positive'] = False
            else:
                del pdict['is_positive']
        return pdict

    def _get_brief_action(self, per_page=50, **kwargs):
        """
        Gets list with Model's weighted parameters with pagination.
        """
        def get_weights(is_positive, page):
            model_id = kwargs.get('model_id')
            return self.Model.find({'model_id': model_id,
                                    'is_positive': is_positive}, query_fields).\
                sort('value', -1 if is_positive else 1 ).\
                skip((page - 1) * per_page).limit(per_page)

        paging_params = (('ppage', int), ('npage', int),)
        params = self._parse_parameters(self.GET_PARAMS + paging_params)

        # Paginate weights
        ppage = params.get('ppage') or 1
        npage = params.get('npage') or 1
        query_fields, show_fields = self._get_fields(params)
        context = {'positive_weights': get_weights(True, ppage),
                   'negative_weights': get_weights(False, npage)}
        return self._render(context)

api.add_resource(WeightsResource, '/cloudml/weights/\
<regex("[\w\.]*"):model_id>/')


class WeightsTreeResource(BaseResource):
    """
    Model Parameters weights categories/weights API methods

    NOTE: it used for constructing tree of model parameters.
    """

    FILTER_PARAMS = (('parent', str), )

    def _list(self, **kwargs):
        """
        """
        params = self._parse_parameters(self.FILTER_PARAMS)
        kwargs['parent'] = params.get('parent') or ''

        categories = app.db.WeightsCategory.find(kwargs,
                                                 ('short_name', 'name'))
        weights = app.db.Weight.find(kwargs, ('name', 'value',
                                              'css_class', 'short_name'))
        context = {'categories': categories, 'weights': weights}
        return self._render(context)

api.add_resource(WeightsTreeResource,
                 '/cloudml/weights_tree/<regex("[\w\.]*"):model_id>',
                 add_standard_urls=False)


class ImportHandlerResource(BaseResource):
    """
    Import handler API methods
    """
    @property
    def Model(self):
        return app.db.ImportHandler

    OBJECT_NAME = 'import_handler'
    post_form = ImportHandlerAddForm
    put_form = ImportHandlerEditForm
    GET_ACTIONS = ('download', )

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(ImportHandlerResource, self).get(*args, **kwargs)

    def _get_download_action(self, **kwargs):
        """
        Downloads importhandler data file.
        """
        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        content = json.dumps(model.data)
        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; \
filename=importhandler-%s.json' % model.name
        return resp

api.add_resource(ImportHandlerResource, '/cloudml/importhandlers/')


class DataSetResource(BaseResource):
    """
    DataSet API methods
    """
    @property
    def Model(self):
        return app.db.DataSet

    OBJECT_NAME = 'dataset'
    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('generate_url', )
    PUT_ACTIONS = ('reupload', 'reimport')
    post_form = DataSetAddForm
    put_form = DataSetEditForm

    def _get_generate_url_action(self, **kwargs):
        ds = self._get_details_query(None, None, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        url = ds.get_s3_download_url()
        return self._render({self.OBJECT_NAME: ds._id,
                             'url': url})

    def _put_reupload_action(self, **kwargs):
        from api.tasks import upload_dataset
        dataset = self._get_details_query(None, None, **kwargs)
        if dataset.status == dataset.STATUS_ERROR:
            dataset.status = dataset.STATUS_IMPORTING
            dataset.save()
            upload_dataset.delay(str(dataset._id))
        return self._render(self._get_save_response_context(
            dataset, extra_fields=['status']))

    def _put_reimport_action(self, **kwargs):
        from api.tasks import import_data
        dataset = self._get_details_query(None, None, **kwargs)
        if dataset.status not in (dataset.STATUS_IMPORTING,
                                  dataset.STATUS_UPLOADING):
            dataset.status = dataset.STATUS_IMPORTING
            dataset.save()
            import_data.delay(dataset_id=str(dataset._id))

        return self._render(self._get_save_response_context(
            dataset, extra_fields=['status']))

api.add_resource(DataSetResource, '/cloudml/importhandlers/\
<regex("[\w\.]*"):import_handler_id>/datasets/')


class Tests(BaseResource):
    """
    Tests API Resource
    """
    OBJECT_NAME = 'test'
    DEFAULT_FIELDS = ('_id', 'name')
    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('confusion_matrix', 'exports', 'examples_size')

    post_form = AddTestForm

    @property
    def Model(self):
        return app.db.Test

    def _get_list_query(self, params, fields, **kwargs):
        params = self._prepare_filter_params(params)
        params['model_id'] = kwargs.get('model_id')
        return self.Model.find(params, fields)

    def _get_details_query(self, params, fields, **kwargs):
        model_id = kwargs.get('model_id')
        test_id = kwargs.get('_id')
        return self.Model.find_one({'model_id': model_id,
                                   '_id': ObjectId(test_id)}, fields)

    def _get_examples_size_action(self, **kwargs):
        fields = ['name', 'model_name', 'model_id', 'examples_size', 'created_on',
                  'created_by']
        tests = app.db.Test.find({}, fields).sort([('examples_size', -1)]).limit(10)
        return self._render({'tests': tests})

    def _get_confusion_matrix_action(self, **kwargs):
        from api.tasks import calculate_confusion_matrix

        parser = reqparse.RequestParser()
        parser.add_argument('weight0', type=float)
        parser.add_argument('weight1', type=float)
        args = parser.parse_args()

        test = self._get_details_query(None, None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        model = app.db.Model.find_one(
            {'_id': ObjectId(kwargs.get('model_id'))})
        if not model:
            raise NotFound('Model not found')

        try:
            calculate_confusion_matrix.delay(
                str(test._id), args.get('weight0'), args.get('weight1'))
        except Exception as e:
            return self._render({self.OBJECT_NAME: str(test._id),
                                 'error': e.message})

        return self._render({self.OBJECT_NAME: str(test._id)})

    def _get_exports_action(self, **kwargs):
        test = self._get_details_query(None, None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        exports = [ex for ex in test.exports
                   if ex['expires'] > datetime.now()]

        return self._render({self.OBJECT_NAME: test._id,
                             'exports': exports})


api.add_resource(Tests, '/cloudml/models/<regex("[\w\.]*"):model_id>/tests/')


REDUCE_FUNC = 'function(obj, prev) {\
                            prev.list.push({"label": obj.pred_label,\
                            "pred": obj.label, "prob": obj.prob})\
                      }'


class TestExamplesResource(BaseResourceSQL):
    """
    """
    @property
    def Model(self):
        return TestExampleSql

    OBJECT_NAME = 'data'
    NEED_PAGING = True
    GET_ACTIONS = ('groupped', 'csv', 'datafields')
    FILTER_PARAMS = [('label', str), ('pred_label', str)]

    def _list(self, **kwargs):
        test = app.db.Test.find_one({'_id': ObjectId(kwargs.get('test_id'))})
        if not test.dataset is None:
            for field in test.dataset.data_fields:
                field_new = field.replace('.', '->')
                self.FILTER_PARAMS.append(("data_input->>'%s'" % field_new, str))
        return super(TestExamplesResource, self)._list(**kwargs)

    def _get_details_query(self, params, fields, **kwargs):
        load_weights = False
        if 'weighted_data_input' in fields:
            fields = None  # We need all fields to recalc weights
            load_weights = True

        example = super(TestExamplesResource, self)._get_details_query(
            params, fields, **kwargs)

        if example is None:
            raise NotFound()

        if load_weights and not example.is_weights_calculated:
            example.calc_weighted_data()
            example = super(TestExamplesResource, self)._get_details_query(
                params, fields, **kwargs)

        # TODO: hack
        example.__dict__['test'] = example.test

        return example

    def _get_groupped_action(self, **kwargs):
        """
        Groups data by `group_by_field` field and calculates mean average
        precision.
        Note: `group_by_field` should be specified in request parameters.
        """
        from ml_metrics import apk
        import numpy as np
        from operator import itemgetter
        logging.info('Start request for calculating MAP')

        group_by_field, count = parse_map_params()
        if not group_by_field:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'field parameter is required')

        res = []
        avps = []
        collection = app.db.TestExample.collection
        groups = collection.group([group_by_field, ],
                                  {'model_id': kwargs.get('model_id'),
                                   'test_id': kwargs.get('test_id')},
                                  {'list': []}, REDUCE_FUNC)

        import sklearn.metrics as sk_metrics
        import numpy
        if len(groups) < 1:
            logging.error('Can not group')
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Can not group')
        if not 'prob' in groups[0]['list'][0]:
            logging.error('Examples do not contain probabilities')
            return odesk_error_response(400, ERR_INVALID_DATA, 'Examples do \
not contain probabilities')
        if not isinstance(groups[0]['list'][0]['prob'], list):
            logging.error('Examples do not contain probabilities')
            return odesk_error_response(400, ERR_INVALID_DATA, 'Examples do \
not contain probabilities')

        if groups[0]['list'][0]['label'] in ("True", "False"):
            transform = lambda x: int(bool(x))
        elif groups[0]['list'][0]['label'] in ("0", "1"):
            transform = lambda x: int(x)
        else:
            logging.error('Type of labels do not support')
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Type of labels do not support')
        logging.info('Calculating avps for groups')
        for group in groups:
            group_list = group['list']

            #print group_list
            labels = [transform(item['label']) for item in group_list]
            pred_labels = [transform(item['pred']) for item in group_list]
            probs = [item['prob'][1] for item in group_list]
            if len(labels) > 1:
                labels = numpy.array(labels)
                probs = numpy.array(probs)
                try:
                    precision, recall, thresholds = \
                        sk_metrics.precision_recall_curve(labels, probs)
                    avp = sk_metrics.auc(recall[:count], precision[:count])
                except:
                    avp = apk(labels, pred_labels, count)
            else:
                avp = apk(labels, pred_labels, count)
            avps.append(avp)
            res.append({'group_by_field': group[group_by_field],
                        'count': len(group_list),
                        'avp': avp})

        res = sorted(res, key=itemgetter("count"), reverse=True)[:100]
        logging.info('Calculating map')
        mavp = np.mean(avps)

        context = {self.list_key: {'items': res},
                   'field_name': group_by_field,
                   'mavp': mavp}
        logging.info('End request for calculating MAP')
        return self._render(context)

    def _get_datafields_action(self, **kwargs):
        fields = [field.replace('.', '->') for field in
                  self._get_datafields(**kwargs)]
        return self._render({'fields': fields})

    def _get_csv_action(self, **kwargs):
        """
        Returns list of examples in csv format
        """
        logging.info('Download examples in csv')

        from api.tasks import get_csv_results

        parser = reqparse.RequestParser()
        parser.add_argument('show', type=str)
        params = parser.parse_args()
        fields, show_fields = self._get_fields(params)
        logging.info('Use fields %s' % str(fields))

        test = app.db.Test.find_one({
            '_id': ObjectId(kwargs.get('test_id')),
            'model_id': kwargs.get('model_id')
        })
        if not test:
            raise NotFound('Test not found')

        get_csv_results.delay(
            test.model_id, str(test._id),
            fields
        )
        return self._render({})

    def _get_datafields(self, **kwargs):
        test = app.db.Test.find_one({'_id': ObjectId(kwargs.get('test_id'))})
        return test.dataset.data_fields

api.add_resource(TestExamplesResource, '/cloudml/models/\
<regex("[\w\.]*"):model_id>/tests/<regex("[\w\.]*"):test_id>/examples/')


class CompareReportResource(BaseResource):
    """
    Resource which generated compare 2 tests report
    """
    ALLOWED_METHODS = ('get', 'options')
    GET_PARAMS = (('model1', str),
                  ('test1', str),
                  ('model2', str),
                  ('test2', str),)

    def _is_list_method(self, **kwargs):
        return False

    def _details(self, extra_params=(), **kwargs):
        from flask import request
        params_pairs = {}

        def process_val(key, val, val_type):
            if key.startswith(val_type):
                index = key.replace(val_type, '')
                if not index in params_pairs:
                    params_pairs[index] = {}
                params_pairs[index][val_type] = val

        for key, val in request.values.iteritems():
            process_val(key, val, 'model')
            process_val(key, val, 'test')

        test_fields = ('name', 'model_name', 'accuracy', 'metrics',
                       'model_id', 'parameters', 'examples_count')
        examples_fields = ('name', 'label', 'pred_label',
                           'weighted_data_input')
        resp_data = []
        for index, item in params_pairs.iteritems():
            test = app.db.Test.find_one({'model_id': item['model'],
                                         '_id': ObjectId(item['test'])},
                                        test_fields)
            examples = app.db.TestExample.find({'model_id': item['model'],
                                                'test_id': item['test']},
                                               examples_fields).limit(10)
            resp_data.append({'test': test, 'examples': examples})
        return self._render({'data': resp_data})

api.add_resource(CompareReportResource,
                 '/cloudml/reports/compare/',
                 add_standard_urls=False)


class Predict(BaseResource):  # pragma: no cover
    ALLOWED_METHODS = ('post', 'options')

    def post(self, model, import_handler):

        hndl = app.db.ImportHandler.find_one({'name': import_handler})
        if hndl is None:
            msg = "Import handler %s doesn\'t exist" % import_handler
            logging.error(msg)
            return odesk_error_response(404, ERR_NO_SUCH_MODEL, msg)

        model = app.db.Model.find_one({'name': model})
        if hndl is None:
            msg = "Model %s doesn\'t exist" % model
            logging.error(msg)
            return odesk_error_response(404, ERR_NO_SUCH_MODEL, msg)

        data = [request.form, ]
        # TODO: Fix this dumps -> loads
        plan = ExtractionPlan(json.dumps(hndl.data), is_file=False)
        request_import_handler = RequestImportHandler(plan, data)
        try:
            trainer = model.get_trainer()
        except Exception, exc:
            msg = "Model %s can't be unpickled: %s" % (model.name,
                                                       exc)
            logging.error(msg)
            return odesk_error_response(400, ERR_UNPICKLING_MODEL,
                                        msg, traceback=traceback.format_exc())
        try:
            probabilities = trainer.predict(request_import_handler,
                                            ignore_error=False)
        except Exception, exc:
            msg = "Predict error: %s:%s" % (exc.__class__.__name__, exc)
            logging.error(msg)
            return odesk_error_response(500, ERR_UNPICKLING_MODEL,
                                        msg, traceback=traceback.format_exc())

        prob = probabilities['probs'][0]
        labels = probabilities['labels']
        probs = prob.tolist() if not (prob is None) else []
        labels = labels.tolist() if not (labels is None) else []
        prob, label = sorted(zip(probs, labels),
                             lambda x, y: cmp(x[0], y[0]),
                             reverse=True)[0]
        return self._render({'label': label, 'prob': prob}, code=201)

api.add_resource(Predict, '/cloudml/model/<regex("[\w\.]*"):model_id>/\
<regex("[\w\.]*"):handler_id>/predict', add_standard_urls=False)


class InstanceResource(BaseResource):
    """
    Instances API methods
    """
    MESSAGE404 = "Instance doesn't exist"
    OBJECT_NAME = 'instance'
    PUT_ACTIONS = ('make_default', )

    post_form = InstanceAddForm
    put_form = InstanceEditForm

    @property
    def Model(self):
        return app.db.Instance

api.add_resource(InstanceResource, '/cloudml/aws_instances/')


class LogResource(BaseResource):
    """
    Log API methods
    """
    FILTER_PARAMS = (('type', str), ('level', str), ('params.obj', str))
    MESSAGE404 = "Log doesn't exist"
    OBJECT_NAME = 'log'
    NEED_PAGING = True
    DEFAULT_FIELDS = [u'_id']

    @property
    def Model(self):
        return app.db.LogMessage

    def _prepare_filter_params(self, params):
        params = super(LogResource, self)._prepare_filter_params(params)

        if 'level' in params:
            all_levels = ['CRITICAL', 'ERROR', 'WARN', 'WARNING',
                          'INFO', 'DEBUG', 'NOTSET']
            if params['level'] in all_levels:
                idx = all_levels.index(params['level'])
                levels = [l for i, l in enumerate(all_levels) if i <= idx]
                params['level'] = {'$in': levels}
            else:
                del params['level']

        return params

api.add_resource(LogResource, '/cloudml/logs/')


class TagResource(BaseResource):
    """
    Tags API methods
    """
    MESSAGE404 = "Tag doesn't exist"
    OBJECT_NAME = 'tag'
    DEFAULT_FIELDS = [u'_id']

    @property
    def Model(self):
        return app.db.Tag

api.add_resource(TagResource, '/cloudml/tags/')


class AuthResource(BaseResource):
    """
    User API methods
    """

    @public
    def post(self, action=None, **kwargs):
        if action == 'get_auth_url':
            auth_url, oauth_token, oauth_token_secret =\
                app.db.User.get_auth_url()

            # TODO: Use redis?
            app.db['auth_tokens'].insert({
                'oauth_token': oauth_token,
                'oauth_token_secret': oauth_token_secret,
            })
            logging.debug(
                "User Auth: oauth token %s added to mongo", oauth_token)
            return self._render({'auth_url': auth_url})

        if action == 'authenticate':
            parser = reqparse.RequestParser()
            parser.add_argument('oauth_token', type=str)
            parser.add_argument('oauth_verifier', type=str)
            params = parser.parse_args()

            oauth_token = params.get('oauth_token')
            oauth_verifier = params.get('oauth_verifier')

            logging.debug(
                "User Auth: trying to authenticate with token %s", oauth_token)
            # TODO: Use redis?
            auth = app.db['auth_tokens'].find_one({
                'oauth_token': oauth_token
            })
            if not auth:
                logging.error('User Auth: token %s not found', oauth_token)
                return odesk_error_response(
                    500, 500,
                    'Wrong token: {0!s}'.format(oauth_token))

            oauth_token_secret = auth.get('oauth_token_secret')
            auth_token, user = app.db.User.authenticate(
                oauth_token, oauth_token_secret, oauth_verifier)

            logging.debug(
                'User Auth: Removing token %s from mongo', oauth_token)
            app.db['auth_tokens'].remove({'_id': auth['_id']})

            return self._render({
                'auth_token': auth_token,
                'user': user
            })

        if action == 'get_user':
            user = getattr(request, 'user', None)
            if user:
                return self._render({'user': user})

            return odesk_error_response(401, 401, 'Unauthorized')

        logging.error('User Auth: invalid action %s', action)
        raise NotFound()

api.add_resource(AuthResource, '/cloudml/auth/<regex("[\w\.]*"):action>',
                 add_standard_urls=False)


class StatisticsResource(BaseResource):
    """
    Statistics methods
    """
    @property
    def Model(self):
        raise Exception('Invalid operation')

    def get(self, action=None):
        def get_count_by_status(collection, extra_fields=[]):
            all_count = 0
            if extra_fields:
                from collections import defaultdict
                from bson.code import Code
                reducer = Code("function(obj, prev){prev.count++;}")
                extra_fields.append("status")
                groupped_data = collection.group(
                    key=extra_fields, 
                    condition={}, 
                    initial={"count": 0}, 
                    reduce=reducer
                )
                res = {}
                for item in groupped_data:
                    key = item.pop("status")
                    all_count += item["count"]
                    if key in res:
                        res[key]["count"] += item["count"]
                    else:
                        res[key] = {"count": item["count"],
                                    "data": []}
                    res[key]["data"].append(item)
            else:
                res = collection.aggregate([
                    {"$group": {"_id": "$status", 
                                "count": {"$sum": 1}}}
                ])['result']
                for item in res:
                    all_count += item["count"]
            return {'count': all_count, 'data': res}

        return self._render({'statistics': {
            'models': get_count_by_status(app.db.Model.collection),
            'datasets': get_count_by_status(app.db.DataSet.collection, ["import_handler_id"]),
            'tests': get_count_by_status(app.db.Test.collection, ["model_id", "model_name"])
        }})

api.add_resource(StatisticsResource, '/cloudml/statistics/')


# Features specific resources
class FeatureSetResource(BaseResource):
    """
    Features Set API methods
    """
    MESSAGE404 = "Feature set set doesn't exist"
    OBJECT_NAME = 'set'
    DEFAULT_FIELDS = [u'_id', 'name']
    #post_form = FeatureSetAddForm
    put_form = FeatureSetForm
    GET_ACTIONS = ('download', )

    @property
    def Model(self):
        return app.db.FeatureSet

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(FeatureSetResource, self).get(*args, **kwargs)

    def _get_download_action(self, **kwargs):
        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        data = json.dumps(model.to_dict())
        resp = Response(data)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; filename=%s.json' % model.name
        return resp

api.add_resource(FeatureSetResource, '/cloudml/features/sets/')


class ClassifierResource(BaseResource):
    """
    Classifier API methods
    """
    MESSAGE404 = "Classifier doesn't exist"
    OBJECT_NAME = 'classifier'
    DEFAULT_FIELDS = [u'_id', 'name']
    post_form = put_form = ClassifierForm
    GET_ACTIONS = ('configuration', )

    @property
    def Model(self):
        return app.db.Classifier

    def _get_configuration_action(self, **kwargs):
        from core.trainer.classifier_settings import CLASSIFIERS
        return self._render({'configuration': CLASSIFIERS})

api.add_resource(ClassifierResource, '/cloudml/features/classifiers/')


class NamedFeatureTypeResource(BaseResource):
    """
    Tags API methods
    """
    MESSAGE404 = "Named feature type doesn't exist"
    OBJECT_NAME = 'named_type'
    DEFAULT_FIELDS = [u'_id', 'name']
    put_form = post_form = NamedFeatureTypeAddForm

    @property
    def Model(self):
        return app.db.NamedFeatureType

api.add_resource(NamedFeatureTypeResource, '/cloudml/features/named_types/')


class TransformerResource(BaseResource):
    """
    Transformer API methods
    """
    MESSAGE404 = "transformer doesn't exist"
    OBJECT_NAME = 'transformer'
    DEFAULT_FIELDS = [u'_id', 'name']
    post_form = TransformerForm
    put_form = TransformerForm
    GET_ACTIONS = ('configuration', )
    ALL_FIELDS_IN_POST = True

    @property
    def Model(self):
        return app.db.Transformer

    def _get_configuration_action(self, **kwargs):
        from api.models import TRANSFORMERS
        return self._render({'configuration': TRANSFORMERS})

api.add_resource(TransformerResource, '/cloudml/features/transformers/')


class ScalersResource(BaseResource):
    """
    Scalers API methods
    """
    MESSAGE404 = "Scaler doesn't exist"
    OBJECT_NAME = 'scaler'
    DEFAULT_FIELDS = [u'_id', 'name']
    put_form = post_form = ScalerForm
    GET_ACTIONS = ('configuration', )
    ALL_FIELDS_IN_POST = True

    @property
    def Model(self):
        return app.db.Scaler

    def _get_configuration_action(self, **kwargs):
        from api.models import SCALERS
        return self._render({'configuration': SCALERS})

api.add_resource(ScalersResource, '/cloudml/features/scalers/')


class FeatureResource(BaseResource):
    """
    Feature API methods
    """
    MESSAGE404 = "Feature doesn't exist"
    OBJECT_NAME = 'feature'
    DEFAULT_FIELDS = [u'_id', 'name']
    post_form = FeatureForm
    put_form = FeatureForm

    @property
    def Model(self):
        return app.db.Feature

api.add_resource(FeatureResource, '/cloudml/features/<regex("[\w\.]*"):features_set_id>/items/')


class ParamsResource(BaseResource):
    """
    Parameters API methods
    """
    @property
    def Model(self):
        raise Exception('Invalid operation')

    def get(self, *args, **kwargs):
        from core.trainer.feature_types import FEATURE_TYPE_FACTORIES
        from core.trainer.feature_types import FEATURE_TYPE_DEFAULTS
        from core.trainer.feature_types import FEATURE_PARAMS_TYPES
        _types = [(key, {
            'type': getattr(value, 'python_type', ''),
            'required_params': value.required_params,
            'optional_params': value.optional_params,
            'default_params': value.default_params,
        }) for key, value in FEATURE_TYPE_FACTORIES.items()]
        _conf = {
            'types': dict(_types),
            'params': FEATURE_PARAMS_TYPES,
            'defaults': FEATURE_TYPE_DEFAULTS
        }
        return self._render({'configuration': _conf})

api.add_resource(ParamsResource, '/cloudml/features/params/')


def populate_parser(model, is_requred=False):
    parser = reqparse.RequestParser()
    for param in model.import_params:
        parser.add_argument(param, type=str, required=is_requred)
    return parser


def parse_map_params():
    """
    Parse fieldname to group and count from GET parameters
    """
    parser = reqparse.RequestParser()
    parser.add_argument('count', type=int)
    parser.add_argument('field', type=str)
    params = parser.parse_args()
    group_by_field = params.get('field')
    count = params.get('count', 100)
    return group_by_field, count
