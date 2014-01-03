import logging
from datetime import datetime
from api.async_tasks.models import AsyncTask
from flask import request

from flask.ext.restful import reqparse

from api import api
from api.base.resources import BaseResourceSQL, NotFound, \
    odesk_error_response, ERR_INVALID_DATA
from models import TestResult, TestExample, Model
from forms import AddTestForm
from sqlalchemy import desc


class TestResource(BaseResourceSQL):
    """
    Tests API Resource
    """
    DEFAULT_FIELDS = ('id', 'name')
    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('confusion_matrix', 'exports', 'examples_size')

    Model = TestResult
    post_form = AddTestForm

    def _get_examples_size_action(self, **kwargs):
        fields = ['name', 'model_name', 'model_id', 'examples_size',
                  'created_on', 'created_by']
        tests = TestResult.query.order_by(
            desc(TestResult.examples_size)).limit(10).all()
        return self._render({'tests': tests})

    def _get_confusion_matrix_action(self, **kwargs):
        from tasks import calculate_confusion_matrix

        parser = reqparse.RequestParser()
        parser.add_argument('weight0', type=float)
        parser.add_argument('weight1', type=float)
        args = parser.parse_args()

        test = self._get_details_query(None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        model = Model.query.get(kwargs.get('model_id'))
        if not model:
            raise NotFound('Model not found')

        try:
            calculate_confusion_matrix.delay(
                test.id, args.get('weight0'), args.get('weight1'))
        except Exception as e:
            return self._render({self.OBJECT_NAME: test.id,
                                 'error': e.message})

        return self._render({self.OBJECT_NAME: test.id})

    def _get_exports_action(self, **kwargs):
        test = self._get_details_query(None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        exports = AsyncTask.get_current_by_object(
            test,
            'api.model_tests.tasks.get_csv_results',
        )

        return self._render({self.OBJECT_NAME: test.id,
                             'exports': exports})


api.add_resource(TestResource,
                 '/cloudml/models/<regex("[\w\.]*"):model_id>/tests/')


class TestExampleResource(BaseResourceSQL):
    """
    """
    Model = TestExample

    NEED_PAGING = True
    GET_ACTIONS = ('groupped', 'csv', 'datafields')
    FILTER_PARAMS = (('label', str), ('pred_label', str))

    def _list(self, **kwargs):
        test = TestResult.query.get(kwargs.get('test_result_id'))
        if not test.dataset is None:
            for field in test.dataset.data_fields:
                field_new = field.replace('.', '->')
                self.FILTER_PARAMS += (("data_input->>%s" % field_new, str),)
        return super(TestExampleResource, self)._list(**kwargs)

    def _get_details_query(self, params, **kwargs):
        example = super(TestExampleResource, self)._get_details_query(
            params, **kwargs)

        if example is None:
            raise NotFound()

        if not example.is_weights_calculated:
            example.calc_weighted_data()
            example = super(TestExampleResource, self)._get_details_query(
                params, **kwargs)

        return example

    def _parse_map_params(self):
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

        group_by_field, count = self._parse_map_params()
        if not group_by_field:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'field parameter is required')

        res = []
        avps = []

        groups = TestExample.get_grouped(
            field=group_by_field,
            model_id=kwargs.get('model_id'),
            test_result_id=kwargs.get('test_result_id')
        )

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

        from tasks import get_csv_results

        parser = reqparse.RequestParser()
        parser.add_argument('show', type=str)
        params = parser.parse_args()
        fields = params.get('show', None)
        fields = fields.split(',')
        logging.info('Use fields %s' % str(fields))

        test = TestResult.query.filter_by(
            id=kwargs.get('test_result_id'),
            model_id=kwargs.get('model_id')).one()
        if not test:
            raise NotFound('Test not found')

        get_csv_results.delay(
            test.model_id, test.id,
            fields
        )
        return self._render({})

    def _get_datafields(self, **kwargs):
        test = TestResult.query.get(kwargs.get('test_result_id'))
        return test.dataset.data_fields

api.add_resource(TestExampleResource, '/cloudml/models/\
<regex("[\w\.]*"):model_id>/tests/<regex("[\w\.]*"):test_result_id>/examples/')
