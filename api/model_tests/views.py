"""
Model tests related resources.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import math
from flask.ext.restful import reqparse

from api import api
from api.base.resources import BaseResourceSQL, NotFound, \
    odesk_error_response, ERR_INVALID_DATA
from models import TestResult, TestExample, Model
from forms import AddTestForm, SelectFieldsForCSVForm, ExportToDbForm
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
        parser.add_argument('weights', type=str)
        args = parser.parse_args()

        test = self._get_details_query(None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        model = Model.query.get(kwargs.get('model_id'))
        if not model:
            raise NotFound('Model not found')

        try:
            arg = args.get("weights")
            import json
            json_weights = json.loads(arg)
            if "weights_list" not in json_weights or \
                    not json_weights["weights_list"]:
                raise ValueError("Weights list is empty")

            weights = []
            for w in json_weights["weights_list"]:
                if not ("label" in w and "value" in w):
                    raise ValueError("Weights list is incorrect")
                weights.append((w["label"], float(w["value"])))
            calculate_confusion_matrix.delay(test.id, weights)

        except Exception as e:
            return self._render({self.OBJECT_NAME: test.id,
                                 'error': e.message})

        return self._render({self.OBJECT_NAME: test.id})

    def _get_exports_action(self, **kwargs):
        test = self._get_details_query(None, **kwargs)
        if not test:
            raise NotFound('Test not found')

        return self._render({self.OBJECT_NAME: test.id,
                             'exports': test.exports,
                             'db_exports': test.db_exports})


api.add_resource(TestResource,
                 '/cloudml/models/<regex("[\w\.]*"):model_id>/tests/')


class TestExampleResource(BaseResourceSQL):
    """
    """
    Model = TestExample

    NEED_PAGING = True
    GET_ACTIONS = ('groupped', 'csv', 'datafields')
    PUT_ACTIONS = ('csv_task', 'db_task')
    FILTER_PARAMS = (('label', str), ('pred_label', str))

    def _list(self, **kwargs):
        self.populate_filter_params(kwargs)
        return super(TestExampleResource, self)._list(**kwargs)

    # Support advanced filtering in details page
    # for getting next/previous links
    def _details(self, **kwargs):
        self.populate_filter_params(kwargs)
        return super(TestExampleResource, self)._details(**kwargs)

    def _get_details_parameters(self, extra_params):
        return self._parse_parameters(extra_params + self.GET_PARAMS +
                                      self.FILTER_PARAMS + self.SORT_PARAMS)

    def populate_filter_params(self, kwargs):
        test = TestResult.query.get(kwargs.get('test_result_id'))
        if test.dataset is not None:
            for field in test.dataset.data_fields:
                field_new = field.replace('.', '->')
                self.FILTER_PARAMS += (("data_input->>%s" % field_new, str), )

    def _get_details_query(self, params, **kwargs):
        example = super(TestExampleResource, self)._get_details_query(
            params, **kwargs)

        if example is None:
            raise NotFound()

        fields = self._get_show_fields(params)
        if 'next' in fields or 'previous' in fields:
            from sqlalchemy.sql import select, func, text, bindparam
            from models import db

            filter_params = kwargs.copy()
            filter_params.update(self._prepare_filter_params(params))
            filter_params.pop('id')

            sort_by = params.get('sort_by', None) or 'id'
            is_desc = params.get('order', None) == 'desc'
            fields_to_select = [TestExample.id]
            # TODO: simplify query with specifying WINDOW w
            if 'previous' in fields:
                fields_to_select.append(
                    func.lag(TestExample.id).over(
                        order_by=[sort_by, 'id']).label('prev'))
            if 'next' in fields:
                fields_to_select.append(
                    func.lead(TestExample.id).over(
                        order_by=[sort_by, 'id']).label('next'))
            tbl = select(fields_to_select)
            for name, val in filter_params.iteritems():
                if '->>' in name:  # TODO: refactor this
                    try:
                        splitted = name.split('->>')
                        name = "%s->>'%s'" % (splitted[0], splitted[1])
                    except:
                        logging.warning('Invalid GET param %s', name)
                tbl.append_whereclause("%s='%s'" % (name, val))
            tbl = tbl.cte('tbl')
            select1 = select(['id', 'prev', 'next']).where(
                tbl.c.id == kwargs['id'])
            res = db.engine.execute(select1, id_1=kwargs['id'])
            id_, example.previous, example.next = res.fetchone()

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
        if 'prob' not in groups[0]['list'][0]:
            logging.error('Examples do not contain probabilities')
            return odesk_error_response(400, ERR_INVALID_DATA, 'Examples do \
not contain probabilities')
        if not isinstance(groups[0]['list'][0]['prob'], list):
            logging.error('Examples do not contain probabilities')
            return odesk_error_response(400, ERR_INVALID_DATA, 'Examples do \
not contain probabilities')

        if groups[0]['list'][0]['label'] in ("True", "False"):
            def transform(x):
                return int(bool(x))
        elif groups[0]['list'][0]['label'] in ("0", "1"):
            def transform(x):
                return int(x)
        else:
            logging.error('Type of labels do not support')
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Type of labels do not support')
        logging.info('Calculating avps for groups')
        calc_average = True
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
            if math.isnan(avp):
                calc_average = False
                avp = "Can't be calculated"
            avps.append(avp)
            res.append({'group_by_field': group[group_by_field],
                        'count': len(group_list),
                        'avp': avp})

        res = sorted(res, key=itemgetter("count"), reverse=True)[:100]
        logging.info('Calculating map')
        mavp = np.mean(avps) if calc_average else "N/A"
        context = {self.list_key: {'items': res},
                   'field_name': group_by_field,
                   'mavp': mavp}
        logging.info('End request for calculating MAP')
        return self._render(context)

    def _get_datafields_action(self, **kwargs):
        fields = [field.replace('.', '->') for field in
                  self._get_datafields(**kwargs)]
        return self._render({'fields': fields})

    def _put_csv_task_action(self, model_id, test_result_id):
        """
        Schedules a task to generate examples in CSV format
        """
        test = TestResult.query.get(test_result_id)
        if not test:
            raise NotFound('Test not found')

        form = SelectFieldsForCSVForm(obj=test)
        if form.is_valid():
            fields = form.cleaned_data['fields']
            if isinstance(fields, list) and len(fields) > 0:
                from tasks import get_csv_results
                logging.info('Download examples in csv')
                get_csv_results.delay(test.model_id, test.id, fields)
                return self._render({})

        return odesk_error_response(400, ERR_INVALID_DATA,
                                    'Fields of the CSV export is required')

    def _put_db_task_action(self, model_id, test_result_id):
        """
        Schedules a task to export examples to the specified DB
        """
        test = TestResult.query.get(test_result_id)
        if not test:
            raise NotFound('Test not found')

        form = ExportToDbForm(obj=test)
        if form.is_valid():
            fields = form.cleaned_data['fields']
            datasource = form.cleaned_data['datasource']
            tablename = form.cleaned_data['tablename']
            if isinstance(fields, list) and len(fields) > 0:
                from tasks import export_results_to_db
                logging.info('Export examples to db')
                export_results_to_db.delay(
                    test.model_id, test.id, datasource.id, tablename, fields)
                return self._render({})

        return odesk_error_response(400, ERR_INVALID_DATA,
                                    'Fields of the DB export is required')

    def _get_datafields(self, **kwargs):
        test = TestResult.query.get(kwargs.get('test_result_id'))
        return test.dataset.data_fields

    def _get_model_list_context(self, models, params):
        context = super(TestExampleResource,
                        self)._get_model_list_context(models, params)
        extra_fields = []
        if models:
            model_item = models[0]
            if model_item.example_id != TestExample.NOT_FILED_ID:
                extra_fields.append('example_id')
            if model_item.name != TestExample.NONAME:
                extra_fields.append('name')
        context['extra_fields'] = extra_fields
        return context

api.add_resource(TestExampleResource, '/cloudml/models/\
<regex("[\w\.]*"):model_id>/tests/<regex("[\w\.]*"):test_result_id>/examples/')
