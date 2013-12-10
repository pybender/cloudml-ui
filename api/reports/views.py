# TODO
# class CompareReportResource(BaseResource):
#     """
#     Resource which generated compare 2 tests report
#     """
#     ALLOWED_METHODS = ('get', 'options')
#     GET_PARAMS = (('model1', str),
#                   ('test1', str),
#                   ('model2', str),
#                   ('test2', str),)

#     def _is_list_method(self, **kwargs):
#         return False

#     def _details(self, extra_params=(), **kwargs):
#         from flask import request
#         params_pairs = {}

#         def process_val(key, val, val_type):
#             if key.startswith(val_type):
#                 index = key.replace(val_type, '')
#                 if not index in params_pairs:
#                     params_pairs[index] = {}
#                 params_pairs[index][val_type] = val

#         for key, val in request.values.iteritems():
#             process_val(key, val, 'model')
#             process_val(key, val, 'test')

#         test_fields = ('name', 'model_name', 'accuracy', 'metrics',
#                        'model_id', 'parameters', 'examples_count')
#         examples_fields = ('name', 'label', 'pred_label',
#                            'weighted_data_input')
#         resp_data = []
#         for index, item in params_pairs.iteritems():
#             test = app.db.Test.find_one({'model_id': item['model'],
#                                          '_id': ObjectId(item['test'])},
#                                         test_fields)
#             examples = app.db.TestExample.find({'model_id': item['model'],
#                                                 'test_id': item['test']},
#                                                examples_fields).limit(10)
#             resp_data.append({'test': test, 'examples': examples})
#         return self._render({'data': resp_data})

# api.add_resource(CompareReportResource,
#                  '/cloudml/reports/compare/',
#                  add_standard_urls=False)