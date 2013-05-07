import json
import logging
import cPickle as pickle
import traceback
from flask.ext.restful import reqparse
from flask import request
from werkzeug.datastructures import FileStorage
from bson.objectid import ObjectId

from api import api, app
from api.utils import crossdomain, ERR_INVALID_DATA, odesk_error_response, \
    ERR_NO_SUCH_MODEL, ERR_UNPICKLING_MODEL
from api.resources import BaseResource, NotFound, ValidationError
from core.trainer.store import load_trainer
from core.trainer.trainer import Trainer, InvalidTrainerFile
from core.trainer.config import FeatureModel, SchemaException
from core.importhandler.importhandler import ExtractionPlan, \
    RequestImportHandler, ImportHandlerException
from api.models import Model, Test, TestExample, ImportHandler

model_parser = reqparse.RequestParser()
model_parser.add_argument('importhandler', required=True, type=str,
                          default=None)
model_parser.add_argument('train_importhandler', type=str)
model_parser.add_argument('features', type=str)
model_parser.add_argument('trainer', type=FileStorage, location='files')


class Models(BaseResource):
    """
    Models API methods
    """
    GET_ACTIONS = ('weights', )
    PUT_ACTIONS = ('train', )
    FILTER_PARAMS = (('status', str), ('comparable', int))
    methods = ('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')

    MESSAGE404 = "Model with name %(name)s doesn't exist"

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

    def _get_weights_action(self, per_page=50, **kwargs):
        """
        Gets list with Model's weighted parameters with pagination.
        """
        paging_params = (('ppage', int), ('npage', int),)
        params = self._parse_parameters(self.GET_PARAMS + paging_params)

        # Paginate weights
        ppage = params.get('ppage') or 1
        npage = params.get('npage') or 1
        fields = self._get_fields_to_show(params)
        fields_dict = {'positive_weights': {'$slice': [(ppage - 1) * per_page,
                                                       per_page]},
                       'negative_weights': {'$slice': [(npage - 1) * per_page,
                                                       per_page]}}
        for field in fields:
            fields_dict[field] = ""

        model = self._get_details_query(params, fields_dict, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        return self._render({self.OBJECT_NAME: model})

    # POST specific methods

    def _validate_parameters(self, params):
        features = params.get('features')
        trainer = params.get('trainer')
        if not features and not trainer:
            raise ValidationError('Either features, either pickled \
trained model is required')

    def _fill_post_data(self, obj, params, **kwargs):
        """
        Fills Model specific fields when uploading trained model or
        creating new model.
        """
        obj.name = kwargs.get('name')
        if 'features' in params and params['features']:
            # Uploading new model
            try:
                feature_model = FeatureModel(params['features'], is_file=False)
            except SchemaException, exc:
                raise ValidationError('Invalid features: %s' % exc)

            trainer = Trainer(feature_model)
            obj.save()
            obj.set_trainer(trainer)

            obj.features = json.loads(params['features'])
        else:
            # Uploading trained model
            try:
                trainer = load_trainer(params['trainer'])
            except InvalidTrainerFile, exc:
                raise ValidationError('Invalid trainer: %s' % exc)
            obj.status = obj.STATUS_TRAINED
            obj.save()
            obj.set_trainer(trainer)
            obj.set_weights(**trainer.get_weights())

        try:
            obj.train_importhandler = obj.importhandler = \
                json.loads(params['importhandler'])
            plan = ExtractionPlan(params['importhandler'], is_file=False)
        except (ValueError, ImportHandlerException) as exc:
            raise ValidationError('Invalid Import Handler: %s' % exc)

        obj.import_params = plan.input_params
        obj.save()

    # PUT specififc methods

    def _fill_put_data(self, model, param, **kwargs):
        importhandler = None
        train_importhandler = None
        if param['importhandler'] and \
                not param['importhandler'] == 'undefined':
            importhandler = json.loads(param['importhandler'])
        if param['train_importhandler'] and \
                not param['train_importhandler'] == 'undefined':
            train_importhandler = json.loads(param['train_importhandler'])
        model.importhandler = importhandler or model.importhandler
        model.train_importhandler = train_importhandler \
            or model.train_importhandler
        model.save()
        return model

    def _put_train_action(self, **kwargs):
        from api.tasks import train_model
        model = self._get_details_query(None, None,
                                        **kwargs)
        parser = populate_parser(model)
        params = parser.parse_args()
        train_model.delay(model.name, params)
        model.status = model.STATUS_QUEUED
        model.save()

        return self._render({self.OBJECT_NAME: model._id})

api.add_resource(Models, '/cloudml/model/<regex("[\w\.]*"):name>',
                 '/cloudml/model/<regex("[\w\.]+"):name>/\
<regex("[\w\.]+"):action>')


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

    @classmethod
    def _get_model_parser(cls):
        if not hasattr(cls, "_model_parser"):
            parser = reqparse.RequestParser()
            parser.add_argument('data', type=str)
            parser.add_argument('type', type=str)
            cls._model_parser = parser
        return cls._model_parser

    def _fill_post_data(self, obj, params, name):
        obj.name = name
        obj.type = params.get('type')
        obj.data = json.loads(params.get('data'))
        obj.save()

api.add_resource(ImportHandlerResource,
                 '/cloudml/import/handler/<regex("[\w\.]*"):name>')


class Tests(BaseResource):
    """
    Tests API Resource
    """
    OBJECT_NAME = 'test'
    FILTER_PARAMS = (('status', str), )
    methods = ('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')

    @property
    def Model(self):
        return app.db.Test

    def _get_list_query(self, params, fields, **kwargs):
        params = self._prepare_filter_params(params)
        params['model_name'] = kwargs.get('model')
        return self.Model.find(params, fields)

    def _get_details_query(self, params, fields, **kwargs):
        model_name = kwargs.get('model')
        test_name = kwargs.get('name')
        return self.Model.find_one({'model_name': model_name,
                                   'name': test_name}, fields)

    def post(self, action=None, **kwargs):
        from api.tasks import run_test
        model_name = kwargs.get('model')
        model = app.db.Model.find_one({'name': model_name})
        parser = populate_parser(model)
        parameters = parser.parse_args()
        test = app.db.Test()
        test.status = test.STATUS_QUEUED
        test.parameters = parameters

        total = app.db.Test.find({'model_name': model.name}).count()
        test.name = "Test%s" % (total + 1)
        test.model_name = model.name
        test.model = model
        test.save(check_keys=False)
        run_test.delay(str(test._id))
        return self._render({self.OBJECT_NAME: test._id}, code=201)

api.add_resource(Tests, '/cloudml/model/<regex("[\w\.]+"):model>/test/\
<regex("[\w\.\-]+"):name>', '/cloudml/model/<regex("[\w\.]+"):model>/tests')


REDUCE_FUNC = 'function(obj, prev) {\
                            prev.list.push({"label": obj.pred_label,\
                            "pred": obj.label})\
                      }'


class TestExamplesResource(BaseResource):
    @property
    def Model(self):
        return app.db.TestExample

    OBJECT_NAME = 'data'
    NEED_PAGING = True
    GET_ACTIONS = ('groupped', )
    DETAILS_PARAM = 'example_id'
    FILTER_PARAMS = (('label', str), ('pred_label', str))
    decorators = [crossdomain(origin='*')]

    def _get_details_query(self, params, fields, **kwargs):
        from helpers.weights import get_weighted_data
        model_name = kwargs.get('model_name')
        test_name = kwargs.get('test_name')
        example_id = kwargs.get('example_id')
        fields.append('data_input')
        example = self.Model.find_one({'model_name': model_name,
                                       'test_name': test_name,
                                       '_id': ObjectId(example_id)})
        if example['weighted_data_input'] == {}:
            model = app.db.Model.find_one({'name': model_name})
            weighted_data_input = get_weighted_data(model,
                                                    example['data_input'])
            example['weighted_data_input'] = dict(weighted_data_input)
            example.save()
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
        model_name = kwargs.get('model_name')
        test_name = kwargs.get('test_name')
        collection = app.db.TestExample.collection
        from bson.code import Code
        _map = Code("emit(this.%s, {pred: this.label,\
                    label: this.label});" % group_by_field)
        _reduce = Code("function (key, values) { \
                         return {'list':  values}; }")
        params = {'model_name': model_name,
                  'test_name': test_name}
        res = []
        avps = []
        result = collection.map_reduce(_map, _reduce, 'avp',
                                       query=params, limit=count)
        for doc in result.find():
            group = doc['value']
            group_list = group['list'] if 'list' in group else [group, ]
            labels = [str(item['label']) for item in group_list]
            pred_labels = [str(item['pred']) for item in group_list]
            avp = apk(labels, pred_labels)
            avps.append(avp)
            res.append({'group_by_field': doc["_id"],
                        'count': len(group_list),
                        'avp': avp})

        res = sorted(res, key=itemgetter("count"), reverse=True)
        mavp = np.mean(avps)

        context = {self.list_key: {'items': res},
                   'field_name': group_by_field,
                   'mavp': mavp}
        return self._render(context)

api.add_resource(TestExamplesResource, '/cloudml/model/\
<regex("[\w\.]+"):model_name>/test/<regex("[\w\.\-]+"):test_name>/data',
                 '/cloudml/model/<regex("[\w\.]+")\
:model_name>/test/<regex("[\w\.\-]+"):test_name>/data/\
<regex("[\w\.\-]+"):example_id>',
                 '/cloudml/model/<regex("[\w\.]+"):model_name>\
/test/<regex("[\w\.\-]+"):test_name>/action/<regex("[\w\.]+"):action>/data')


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
        params = self._parse_parameters(self.GET_PARAMS)
        test_fields = ('name', 'model_name', 'accuracy', 'metrics')
        test1 = app.db.Test.find_one({'model_name': params.get('model1'),
                                      'name': params.get('test1')},
                                     test_fields)
        test2 = app.db.Test.find_one({'model_name': params.get('model2'),
                                      'name': params.get('test2')},
                                     test_fields)
        examples_fields = ('name', 'label', 'pred_label',
                           'weighted_data_input')
        examples1 = app.db.TestExample.find({'model_name': params.get('model1'),
                                             'test_name': params.get('test1')},
                                            examples_fields).limit(10)
        examples2 = app.db.TestExample.find({'model_name': params.get('model2'),
                                             'test_name': params.get('test2')},
                                            examples_fields).limit(10)
        return self._render({'test1': test1, 'test2': test2,
                             'examples1': examples1,
                             'examples2': examples2})

api.add_resource(CompareReportResource, '/cloudml/reports/compare')


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
            if model.trainer:
                trainer = pickle.loads(model.trainer)
            else:
                trainer = pickle.loads(model.fs.trainer)
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

api.add_resource(Predict, '/cloudml/model/<regex("[\w\.]*"):model>/\
<regex("[\w\.]*"):import_handler>/predict')


def populate_parser(model):
    parser = reqparse.RequestParser()
    for param in model.import_params:
        parser.add_argument(param, type=str)
    return parser
