from flask import request

from api import api
from api.base.resources import BaseResourceSQL
from api.model_tests.models import TestResult, TestExample


class CompareReportResource(BaseResourceSQL):
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
            test = TestResult.query.filter_by(id=item['test'],
                                              model_id=item['model']).one()
            examples = TestExample.query.filter_by(
                test_result=test, model_id=item['model']).limit(10).all()
            resp_data.append({'test': test, 'examples': examples})
        return self._render({'data': resp_data})

api.add_resource(CompareReportResource, '/cloudml/reports/compare/',
                 add_standard_urls=False)
