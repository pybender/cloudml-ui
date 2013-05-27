import json
import logging
import cPickle as pickle
import traceback
import StringIO
import csv
from flask.ext.restful import reqparse
from flask import request, Response

import gevent
from pymongo.errors import OperationFailure
from werkzeug.datastructures import FileStorage
from bson.objectid import ObjectId

from api import api, app
from api.utils import crossdomain, ERR_INVALID_DATA, odesk_error_response, \
    ERR_NO_SUCH_MODEL, ERR_UNPICKLING_MODEL
from api.resources import BaseResource, NotFound, ValidationError
from api.forms import ModelAddForm, ModelEditForm, ImportHandlerAddForm, \
    AddTestForm, AwsInstanceAddForm
from core.importhandler.importhandler import ExtractionPlan, RequestImportHandler

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
    GET_ACTIONS = ('download', 'reload' )
    PUT_ACTIONS = ('train', )
    FILTER_PARAMS = (('status', str), ('comparable', int))
    DEFAULT_FIELDS = ('_id', 'name')
    methods = ('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')

    MESSAGE404 = "Model with name %(_id)s doesn't exist"

    post_form = ModelAddForm
    put_form = ModelEditForm

    DOWNLOAD_FIELDS = ('trainer', 'importhandler',
                       'train_importhandler', 'features')

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
        return pdict

    def _get_reload_action(self, **kwargs):
        from api.tasks import fill_model_parameter_weights
        model = self._get_details_query(None, None,
                                        **kwargs)
        fill_model_parameter_weights.delay(str(model._id), True)
        return self._render({self.OBJECT_NAME: model._id})

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
            content = json.dumps(getattr(model, 'importhandler'))

        filename = "%s-%s.%s" % (model.name, field,
                                 'dat' if field == 'trainer' else 'json')

        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
        return resp

    # POST specific methods

    def _put_train_action(self, **kwargs):
        from api.tasks import train_model
        model = self._get_details_query(None, None,
                                        **kwargs)
        parser = populate_parser(model, is_requred=True)
        parser.add_argument('aws_instance', type=str, required=True)
        params = parser.parse_args()
        model.status = model.STATUS_QUEUED
        model.save()

        # Get AWS Instance
        instance_id = params.get('aws_instance')
        instance = app.db.AwsInstance.find({'_id': ObjectId(instance_id)})
        if instance is None:
            raise NotFound('AWS Instance not found')

        train_model.delay(str(model._id), params)
        return self._render({self.OBJECT_NAME: model._id})

api.add_resource(Models, '/cloudml/models/')


class WeightsResource(BaseResource):
    """
    Model Parameters weights API methods
    """
    GET_ACTIONS = ('brief', )
    ENABLE_FULLTEXT_SEARCH = True
    OBJECT_NAME = 'weight'
    methods = ('GET', )
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
                                    'is_positive': is_positive}, fields).\
                skip(page * per_page).limit(per_page)

        paging_params = (('ppage', int), ('npage', int),)
        params = self._parse_parameters(self.GET_PARAMS + paging_params)

        # Paginate weights
        ppage = params.get('ppage') or 1
        npage = params.get('npage') or 1
        fields = self._get_fields_to_show(params)
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
    methods = ('GET', )

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
    decorators = [crossdomain(origin='*')]
    methods = ['GET', 'OPTIONS', 'PUT', 'POST']
    post_form = ImportHandlerAddForm

api.add_resource(ImportHandlerResource, '/cloudml/importhandlers/')


class Tests(BaseResource):
    """
    Tests API Resource
    """
    OBJECT_NAME = 'test'
    DEFAULT_FIELDS = ('_id', 'name')
    FILTER_PARAMS = (('status', str), )
    methods = ('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')
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
    FILTER_PARAMS = (('label', str), ('pred_label', str))
    decorators = [crossdomain(origin='*')]

    def _get_details_query(self, params, fields, **kwargs):
        # TODO: return only fields that are specified
        example = super(TestExamplesResource, self).\
            _get_details_query(params, None, **kwargs)
        if example is None:
            raise NotFound('Example not found')

        from helpers.weights import get_weighted_data
        if example['weighted_data_input'] == {}:
            model = app.db.Model.find_one({'_id': ObjectId(kwargs['model_id'])})
            weighted_data_input = get_weighted_data(model,
                                                    example['data_input'])
            example['weighted_data_input'] = dict(weighted_data_input)
            example.save(check_keys=False)
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

        collection = app.db.TestExample.collection

        res = []
        avps = []

        # from bson.code import Code
        # _map = Code("emit(this.%s, {pred: this.label,\
        #             label: this.label});" % group_by_field)
        # _reduce = Code("function (key, values) { \
        #                  return {'list':  values}; }")
        # params = {'model_name': model_name,
        #           'test_name': test_name}
        # result = collection.map_reduce(_map, _reduce, 'avp',
        #                                query=params)

        # for doc in result.find():
        #     group = doc['value']
        #     group_list = group['list'] if 'list' in group else [group, ]
        #     labels = [str(item['label']) for item in group_list]
        #     pred_labels = [str(item['pred']) for item in group_list]
        #     avp = apk(labels, pred_labels, count)
        #     avps.append(avp)
        #     res.append({'group_by_field': doc["_id"],
        #                 'count': len(group_list),
        #                 'avp': avp})

        groups = collection.group([group_by_field, ],
                                  {'model_id': model_id,
                                   'test_id': test_id},
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
        example = self.Model.find_one(kwargs, ('data_input', ))
        data = example['data_input']
        return self._render({'fields': data.keys()})

    def _get_csv_action(self, **kwargs):
        """
        Returns list of examples in csv format
        """
        def generate():
            parser_params = self.GET_PARAMS + self.FILTER_PARAMS
            params = self._parse_parameters(parser_params)
            fields = self._get_fields_to_show(params)

            kw = dict([(k, v) for k, v in kwargs.iteritems() if v])
            examples = self._get_list_query(params, None, **kw)
            fout = StringIO.StringIO()
            writer = csv.writer(fout, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerow(fields)
            for example in examples:
                rows = []
                for name in fields:
                    # TODO: This is a quick hack. Fix it!
                    if name.startswith('data_input'):
                        feature_name = name.replace('data_input.', '')
                        val = example['data_input'][feature_name]
                    else:
                        val = example[name] if name in example else ''
                    rows.append(val)
                writer.writerow(rows)
            return fout.getvalue()

        from flask import Response
        resp = Response(generate(), mimetype='text/csv')
        resp.headers["Content-Disposition"] = "attachment; \
filename=%(model_id)s-%(test_id)s-examples.csv" % kwargs
        return resp

api.add_resource(TestExamplesResource, '/cloudml/models/\
<regex("[\w\.]*"):model_id>/tests/<regex("[\w\.]*"):test_id>/examples/')


class CompareReportResource(BaseResource):
    """
    Resource which generated compare 2 tests report
    """
    ALLOWED_METHODS = ('get', )
    decorators = [crossdomain(origin='*')]
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
    ALLOWED_METHODS = ('post', )
    decorators = [crossdomain(origin='*')]

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


class AwsInstanceResource(BaseResource):
    """
    AWS Instances API methods
    """
    MESSAGE404 = "AWS Instance doesn't exist"
    OBJECT_NAME = 'instance'
    decorators = [crossdomain(origin='*')]
    methods = ['GET', 'OPTIONS', 'PUT', 'POST']
    post_form = AwsInstanceAddForm

    @property
    def Model(self):
        return app.db.AwsInstance

api.add_resource(AwsInstanceResource, '/cloudml/aws_instances/')


def populate_parser(model, is_requred=False):
    parser = reqparse.RequestParser()
    for param in model.import_params:
        parser.add_argument(param, type=str, required=is_requred)
    return parser
