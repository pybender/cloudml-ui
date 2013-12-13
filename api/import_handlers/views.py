import json
from flask import Response
from sqlalchemy.orm import undefer

from api import api
from api.base.resources import BaseResourceSQL, NotFound, public_actions
from models import ImportHandler, DataSet
from forms import ImportHandlerAddForm, ImportHandlerEditForm, \
    DataSetAddForm, DataSetEditForm


class ImportHandlerResource(BaseResourceSQL):
    """
    Import handler API methods
    """
    Model = ImportHandler

    post_form = ImportHandlerAddForm
    put_form = ImportHandlerEditForm
    GET_ACTIONS = ('download', )

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(ImportHandlerResource, self).get(*args, **kwargs)

    def _modify_details_query(self, cursor, params):
        return cursor.options(undefer('data'))

    def _get_download_action(self, **kwargs):
        """
        Downloads importhandler data file.
        """
        model = self._get_details_query(None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        content = json.dumps(model.data)
        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; \
filename=importhandler-%s.json' % model.name
        return resp

api.add_resource(ImportHandlerResource, '/cloudml/importhandlers/')


# class ImportHandlerResource(BaseResource):
#     """
#     Import handler API methods
#     """
#     @property
#     def Model(self):
#         return app.db.ImportHandler

#     OBJECT_NAME = 'import_handler'
#     post_form = AddImportHandlerForm
#     GET_ACTIONS = ('download',)
#     PUT_ACTIONS = ('run_sql', 'test_handler')
#     FORCE_FIELDS_CHOOSING = True

#     HANDLER_REGEXP = re.compile('^[a-zA-Z_]+$')
#     DATASOURCE_REGEXP = re.compile('^datasource.[-\d]+.[a-zA-Z_]+')
#     QUERY_REGEXP = re.compile('^queries.[-\d]+.[a-zA-Z_]+$')
#     ITEM_REGEXP = re.compile(
#         '^queries.[-\d]+.items.[-\d]+.[a-zA-Z_]+$')
#     FEATURE_REGEXP = re.compile(
#         '^queries.[-\d]+.items.[-\d]+.target_features.[-\d]+.[a-zA-Z_]+$')

#     @public_actions(['download'])
#     def get(self, *args, **kwargs):
#         return super(ImportHandlerResource, self).get(*args, **kwargs)

#     def put(self, action=None, **kwargs):
#         if action:
#             return super(ImportHandlerResource, self).put(action, **kwargs)

#         obj = self._get_details_query(None, None, **kwargs)
#         if obj is None:
#             raise NotFound(self.MESSAGE404 % kwargs)

#         data = request.form

#         def edit():
#             # edit handler fields
#             handler_form = None
#             for key, val in data.iteritems():
#                 match = self.HANDLER_REGEXP.search(key)
#                 if match:
#                     if not handler_form:
#                         handler_form = HandlerForm(obj=obj)
#                     handler_form.append_data(key, val)
#             if handler_form is not None and handler_form.is_valid():
#                 handler_form.save()

#             datasource_forms = {}
#             for key, val in data.iteritems():
#                 match = self.DATASOURCE_REGEXP.search(key)
#                 if match:
#                     sub_keys = key.split('.')
#                     ds_num = sub_keys[1]
#                     if not ds_num in datasource_forms:
#                         datasource_forms[ds_num] = HandlerDataSourceForm(
#                             obj.data['datasource'], ds_num)
#                     field = sub_keys[2]
#                     datasource_forms[ds_num].append_data(field, val)

#             for i, form in datasource_forms.iteritems():
#                 if form.is_valid():
#                     form.save()

#             # Add/edit query fields
#             query_forms = {}
#             for key, val in data.iteritems():
#                 match = self.QUERY_REGEXP.search(key)
#                 if match:
#                     sub_keys = key.split('.')
#                     query_num = sub_keys[1]
#                     if not query_num in query_forms:
#                         query_forms[query_num] = QueryForm(
#                             obj.data['queries'], query_num)
#                     field = sub_keys[2]
#                     query_forms[query_num].append_data(field, val)

#             for i, form in query_forms.iteritems():
#                 if form.is_valid():
#                     form.save()

#             # Add/edit query items fields
#             item_forms = {}
#             for key, val in data.iteritems():
#                 match = self.ITEM_REGEXP.search(key)
#                 if match:
#                     sub_keys = key.split('.')
#                     query_num = sub_keys[1]
#                     item_num = sub_keys[3]
#                     num = (query_num, item_num)
#                     if not num in item_forms:
#                         items = obj.data['queries'][int(query_num)]['items']
#                         item_forms[num] = QueryItemForm(
#                             items, item_num)
#                     field = sub_keys[4]
#                     item_forms[num].append_data(field, val)

#             for i, form in item_forms.iteritems():
#                 if form.is_valid():
#                     form.save()

#             # Add/edit target features fields
#             feature_forms = {}
#             for key, val in data.iteritems():
#                 match = self.FEATURE_REGEXP.search(key)
#                 if match:
#                     sub_keys = key.split('.')
#                     query_num = sub_keys[1]
#                     item_num = sub_keys[3]
#                     feature_num = sub_keys[5]
#                     num = (query_num, item_num, feature_num)
#                     if not num in feature_forms:
#                         features = obj.data['queries'][int(query_num)]['items'][int(item_num)]['target_features']
#                         feature_forms[num] = TargetFeatureForm(
#                             features, feature_num)
#                     field = sub_keys[6]
#                     feature_forms[num].append_data(field, val)

#             for i, form in feature_forms.iteritems():
#                 if form.is_valid():
#                     form.save()

#         if 'remove_item' in data:
#             num = int(data.get('num', None))
#             query_num = int(data.get('query_num', None))
#             if num is None or query_num is None:
#                 raise ValidationError('num and query_num are required')
#             del obj.data['queries'][query_num]['items'][num]
#         elif 'remove_query' in data:
#             num = int(data.get('num', None))
#             if num is None:
#                 raise ValidationError('num is required')
#             del obj.data['queries'][num]
#         elif 'remove_feature' in data:
#             num = int(data.get('num', None))
#             query_num = int(data.get('query_num', None))
#             item_num = int(data.get('item_num', None))
#             if num is None:
#                 raise ValidationError('num is required')
#             del obj.data['queries'][query_num]['items'][item_num]['target_features'][num]
#         elif 'fill_predefined' in data:
#             data.get('predefined_selected', None)
#             num = int(data.get('num', None))
#             datasource_id = data.get('datasource', None)
#             ds = app.db.DataSource.get_from_id(ObjectId(datasource_id))
#             obj.data['datasource'][num] = {
#                 'name': ds.name,
#                 'type': ds.type,
#                 'db': ds.db_settings
#             }
#         else:
#             edit()
        
#         obj.save()
#         return self._render(self._get_save_response_context(obj),
#                             code=200)

#     def _get_download_action(self, **kwargs):
#         """
#         Downloads importhandler data file.
#         """
#         model = self._get_details_query(None, None, **kwargs)
#         if model is None:
#             raise NotFound(self.MESSAGE404 % kwargs)

#         data = json.dumps(model.data)
#         resp = Response(data)
#         resp.headers['Content-Type'] = 'text/plain'
#         resp.headers['Content-Disposition'] = 'attachment; filename=importhandler-%s.json' % model.name
#         return resp

#     def _put_run_sql_action(self, **kwargs):
#         """
#         Run sql query for testing
#         """
#         model = self._get_details_query(None, None, **kwargs)
#         if model is None:
#             raise NotFound(self.MESSAGE404 % kwargs)

#         form = QueryTestForm(obj={})
#         if not form.is_valid():
#             return self._render({'error': form.error_messages})

#         sql = form.cleaned_data['sql']
#         limit = form.cleaned_data['limit']
#         params = form.cleaned_data['params']
#         datasource_name = form.cleaned_data['datasource']
#         try:
#             sql = sql % params
#         except (KeyError, ValueError):
#             return odesk_error_response(400, ERR_INVALID_DATA,
#                                         'Wrong query parameters')

#         try:
#             model.check_sql(sql)
#         except Exception as e:
#             return odesk_error_response(400, ERR_INVALID_DATA, str(e))

#         # Change query LIMIT
#         sql = model.build_query(sql, limit=limit)

#         try:
#             data = list(model.execute_sql_iter(sql, datasource_name))
#         except DatabaseError as e:
#             return odesk_error_response(400, ERR_INVALID_DATA, str(e))

#         columns = []
#         if len(data) > 0:
#             columns = data[0].keys()

#         return self._render({'data': data, 'columns': columns, 'sql': sql})

#     def _put_test_handler_action(self, **kwargs):
#         """
#         Run importing data for testing
#         """
#         from core.importhandler.importhandler import ExtractionPlan,\
#             ImportHandler

#         model = self._get_details_query(None, None, **kwargs)
#         if model is None:
#             raise NotFound(self.MESSAGE404 % kwargs)

#         form = ImportHandlerTestForm(obj={})
#         if not form.is_valid():
#             return self._render({'error': form.error_messages})

#         import_params = form.cleaned_data['params']
#         limit = form.cleaned_data['limit']

#         # Change limit for all handler queries
#         for query in model.data['queries']:
#             query['sql'] = model.build_query(query['sql'], limit=limit)

#         try:
#             handler = json.dumps(model.data)
#             plan = ExtractionPlan(handler, is_file=False)
#             handler = ImportHandler(plan, import_params)
#             content = (json.dumps(row, cls=DecimalEncoder) for row in handler)
#             content = '\n'.join(content)
#         except Exception as e:
#             return odesk_error_response(400, ERR_INVALID_DATA, str(e))

#         helper = AmazonS3Helper()
#         name = '{!s}.txt'.format(uuid.uuid4())
#         helper.save_key_string(name, content)
#         return self._render({'url': helper.get_download_url(name, 3600)})

# api.add_resource(ImportHandlerResource, '/cloudml/importhandlers/')


class DataSetResource(BaseResourceSQL):
    """
    DataSet API methods
    """
    Model = DataSet

    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('generate_url', )
    PUT_ACTIONS = ('reupload', 'reimport')
    post_form = DataSetAddForm
    put_form = DataSetEditForm

    def _get_generate_url_action(self, **kwargs):
        ds = self._get_details_query(None, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        url = ds.get_s3_download_url()
        return self._render({self.OBJECT_NAME: ds.id,
                             'url': url})

    def _put_reupload_action(self, **kwargs):
        from api.import_handlers.tasks import upload_dataset
        dataset = self._get_details_query(None, **kwargs)
        if dataset.status == DataSet.STATUS_ERROR:
            dataset.status = DataSet.STATUS_IMPORTING
            dataset.save()
            upload_dataset.delay(dataset.id)
        return self._render({self.OBJECT_NAME: dataset})

    def _put_reimport_action(self, **kwargs):
        from tasks import import_data
        dataset = self._get_details_query(None, **kwargs)
        if dataset.status not in (DataSet.STATUS_IMPORTING,
                                  DataSet.STATUS_UPLOADING):
            dataset.status = DataSet.STATUS_IMPORTING
            dataset.save()
            import_data.delay(dataset_id=dataset.id)

        return self._render({self.OBJECT_NAME: dataset})

api.add_resource(DataSetResource, '/cloudml/importhandlers/\
<regex("[\w\.]*"):import_handler_id>/datasets/')
