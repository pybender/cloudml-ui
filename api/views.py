from collections import defaultdict
from datetime import datetime
import json
import logging
import traceback
from flask.ext.restful import reqparse
from flask import request, Response

import gevent
from pymongo.errors import OperationFailure
from werkzeug.datastructures import FileStorage
from bson.objectid import ObjectId

from api import api, app
from api.decorators import public
from api.utils import ERR_INVALID_DATA, odesk_error_response, \
    ERR_NO_SUCH_MODEL, ERR_UNPICKLING_MODEL, slugify
from api.resources import BaseResource, NotFound, ValidationError
from api.forms import ModelAddForm, ModelEditForm, ImportHandlerAddForm, \
    AddTestForm, InstanceAddForm, InstanceEditForm, ImportHandlerEditForm
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


def event_stream(query_params={}):
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
def sse_request():
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
    FILTER_PARAMS = (('status', str), ('comparable', int), ('tag', str))
    DEFAULT_FIELDS = ('_id', 'name')

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

    def _prepare_filter_params(self, params):
        pdict = super(Models, self)._prepare_filter_params(params)
        if 'comparable' in pdict:
            pdict['comparable'] = bool(pdict['comparable'])
        if 'tag' in pdict:
            pdict['tags'] = {'$in': [pdict['tag']]}
            del pdict['tag']
        return pdict

    def _get_reload_action(self, **kwargs):
        from api.tasks import fill_model_parameter_weights
        model = self._get_details_query(None, None,
                                        **kwargs)
        fill_model_parameter_weights.delay(str(model._id), True)
        return self._render({self.OBJECT_NAME: model._id})

    def _get_by_importhandler_action(self, **kwargs):
        parser_params = self.GET_PARAMS + (('handler', str), )
        params = self._parse_parameters(parser_params)
        query_fields, show_fields = self._get_fields(params)
        _id = ObjectId(params.get('handler'))
        expr = {'$or': [{'test_import_handler._id': _id},
                        {'train_import_handler._id': _id}]}
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
            content = json.dumps(getattr(model, field))

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
                dataset = import_handler.create_dataset(params)
                tasks_list.append(import_data.s(str(dataset._id),
                                                str(model._id)))
            else:
                dataset = form.cleaned_data.get('dataset', None)
            if not spot_instance_type is None:
                tasks_list.append(request_spot_instance.s(instance_type=spot_instance_type,
                                                          model_id=str(model._id)))
                tasks_list.append(get_request_instance.subtask(
                    (),
                    {
                        'callback': 'train',
                        'dataset_id': str(dataset._id),
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
                    train_model_args = (str(dataset._id), str(model._id),
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
                 add_standart_urls=False)


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

    def _get_generate_url_action(self, **kwargs):
        ds = self._get_details_query(None, None, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        url = ds.get_s3_download_url()
        return self._render({self.OBJECT_NAME: ds._id,
                             'url': url})

    def post(self, **kwargs):
        """
        Loads dataset using specified import handler.
        """
        from api.tasks import import_data
        handler_id = kwargs.get('import_handler_id')
        importhandler = app.db.ImportHandler.find_one({'_id': ObjectId(handler_id)})
        if importhandler is None:
            raise NotFound('Import handler not found')

        parser = populate_parser(importhandler, is_requred=True)
        parameters = parser.parse_args()

        dataset = app.db.DataSet()
        str_params = "-".join(["%s=%s" % item
                              for item in parameters.iteritems()])
        dataset.name = "%s: %s" % (importhandler.name, str_params)
        dataset.import_handler_id = str(importhandler._id)
        dataset.import_params = parameters
        dataset.save(validate=True)
        dataset.set_file_path()
        import_data.delay(str(dataset._id))
        return self._render(self._get_save_response_context(dataset),
                            code=201)

api.add_resource(DataSetResource, '/cloudml/importhandlers/\
<regex("[\w\.]*"):import_handler_id>/datasets/')


class Tests(BaseResource):
    """
    Tests API Resource
    """
    OBJECT_NAME = 'test'
    DEFAULT_FIELDS = ('_id', 'name')
    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('confusion_matrix', 'exports')

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
        id = kwargs.get('_id')
        return self.Model.find_one({'model_id': model_id,
                                   '_id': ObjectId(id)}, fields)

    def _get_confusion_matrix_action(self, **kwargs):
        from api.tasks import calculate_confusion_matrix

        parser = reqparse.RequestParser()
        parser.add_argument('weight0', type=float)
        parser.add_argument('weight1', type=float)
        args = parser.parse_args()

        test = self._get_details_query(None, None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        model = app.db.Model.find_one({'_id': ObjectId(kwargs.get('model_id'))})
        if not model:
            raise NotFound('Model not found')

        try:
            result = calculate_confusion_matrix(test._id, args.get('weight0'), args.get('weight1'))
        except Exception as e:
            return self._render({self.OBJECT_NAME: test._id, 'error': e.message})

        result = zip(model.labels, result)

        return self._render({self.OBJECT_NAME: test._id, 'confusion_matrix': result})

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


class TestExamplesResource(BaseResource):
    @property
    def Model(self):
        return app.db.TestExample

    OBJECT_NAME = 'data'
    NEED_PAGING = True
    GET_ACTIONS = ('groupped', 'csv', 'datafields')
    FILTER_PARAMS = [('label', str), ('pred_label', str)]

    def _get_list_query(self, params, fields, **kwargs):
        test = app.db.Test.find_one({'_id': ObjectId(kwargs.get('test_id'))})

        data_input_params = dict([(p, v) for p, v in params.items()
                                  if p.startswith('data_input.') and v])
        if data_input_params:
            params['_id'] = {
                '$in': [e['_id'] for e in test.get_examples_full_data(
                    ['_id'],
                    data_input_params
                )]
            }

            for param in data_input_params:
                params[param] = None

        return super(TestExamplesResource, self)._get_list_query(
            params, fields, **kwargs)

    def _list(self, **kwargs):
        test = app.db.Test.find_one({'_id': ObjectId(kwargs.get('test_id'))})
        if not test.dataset is None:
            for field in test.dataset.data_fields:
                field_new = field.replace('.', '->')
                self.FILTER_PARAMS.append(('data_input.%s' % field_new, str))
        self.FILTER_PARAMS.append(('_id', dict),)
        return super(TestExamplesResource, self)._list(**kwargs)

    def _get_details_query(self, params, fields, **kwargs):
        if 'weighted_data_input' in fields:
            fields += ['vect_data', 'data_input']

        example = super(TestExamplesResource, self).\
            _get_details_query(params, fields, **kwargs)

        if example and 'weighted_data_input' in fields and \
                example['weighted_data_input'] == {} \
                and 'vect_data' in example:
            from api.helpers.features import get_features_vect_data
            model_id = kwargs['model_id']
            model = app.db.Model.find_one({'_id': ObjectId(model_id)})
            feature_model = model.get_trainer()._feature_model
            data = get_features_vect_data(example['vect_data'],
                                          feature_model.features.items(),
                                          feature_model.target_variable)

            from helpers.weights import get_example_params
            model_weights = app.db.Weight.find({'model_id': model_id})
            weighted_data = dict(get_example_params(
                model_weights, example.data_input, data))
            example['weighted_data_input'] = weighted_data
            # FIXME: Find a better way to do it using mongokit
            app.db.TestExample.collection.update(
                {'_id': example['_id']},
                {'$set': {'weighted_data_input': weighted_data}})
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

        # getting from request parameters fieldname to group.
        parser = reqparse.RequestParser()
        parser.add_argument('count', type=int)
        parser.add_argument('field', type=str)
        params = parser.parse_args()
        group_by_field = params.get('field')
        count = params.get('count', 100)
        if not group_by_field:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'field parameter is required')
        model_id = kwargs.get('model_id')
        test_id = kwargs.get('test_id')
        logging.info('For model: %s test: %s' % (model_id, test_id))
        logging.info('Gettings examples')

        res = []
        avps = []

        test = app.db.Test.find_one({'_id': ObjectId(test_id)})
        groups = defaultdict(list)
        example_fields = ['label', 'pred_label', 'prob', 'id']

        for row in test.get_examples_full_data(example_fields):
            groups[row[group_by_field]].append({
                'label': row['pred_label'],
                'pred': row['label'],
                'prob': row['prob'],
            })

        groups = [{
            group_by_field: key,
            'list': value
        } for key, value in groups.iteritems()]

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
                 add_standart_urls=False)


class Predict(BaseResource):
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
<regex("[\w\.]*"):handler_id>/predict', add_standart_urls=False)


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
        from api.auth import AuthException

        if action == 'get_auth_url':
            auth_url, oauth_token, oauth_token_secret =\
                app.db.User.get_auth_url()

            # TODO: Use redis?
            app.db['auth_tokens'].insert({
                'oauth_token': oauth_token,
                'oauth_token_secret': oauth_token_secret,
            })

            return self._render({'auth_url': auth_url})

        if action == 'authenticate':
            parser = reqparse.RequestParser()
            parser.add_argument('oauth_token', type=str)
            parser.add_argument('oauth_verifier', type=str)
            params = parser.parse_args()

            oauth_token = params.get('oauth_token')
            oauth_verifier = params.get('oauth_verifier')

            # TODO: Use redis?
            auth = app.db['auth_tokens'].find_one({
                'oauth_token': oauth_token
            })
            if not auth:
                return odesk_error_response(
                    500, 500,
                    'Wrong token: {0!s}'.format(oauth_token))

            oauth_token_secret = auth.get('oauth_token_secret')
            auth_token, user = app.db.User.authenticate(
                oauth_token, oauth_token_secret, oauth_verifier)

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

        raise NotFound()

api.add_resource(AuthResource, '/cloudml/auth/<regex("[\w\.]*"):action>',
                 add_standart_urls=False)


def populate_parser(model, is_requred=False):
    parser = reqparse.RequestParser()
    for param in model.import_params:
        parser.add_argument(param, type=str, required=is_requred)
    return parser
