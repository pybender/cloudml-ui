import json
import uuid
import re
from flask import Response, request
from sqlalchemy.orm import undefer
from psycopg2._psycopg import DatabaseError

from core.importhandler.importhandler import DecimalEncoder, \
    ImportHandlerException

from api import api
from api.base.models import assertion_msg
from api.base.resources import BaseResourceSQL, NotFound, public_actions, \
    ValidationError, odesk_error_response, ERR_INVALID_DATA
from models import ImportHandler, DataSet, PredefinedDataSource
from forms import ImportHandlerAddForm, DataSetAddForm, \
    DataSetEditForm, PredefinedDataSourceForm


class PredefinedDataSourceResource(BaseResourceSQL):
    """
    Predefined DataSource API methods
    """
    DEFAULT_FIELDS = ['id', 'name', 'db']
    put_form = post_form = PredefinedDataSourceForm

    @property
    def Model(self):
        return PredefinedDataSource

api.add_resource(PredefinedDataSourceResource, '/cloudml/datasources/')


class ImportHandlerResource(BaseResourceSQL):
    """
    Import handler API methods
    """
    Model = ImportHandler

    post_form = ImportHandlerAddForm
    GET_ACTIONS = ('download', )
    PUT_ACTIONS = ('run_sql', 'test_handler')

    HANDLER_REGEXP = re.compile('^[a-zA-Z_]+$')
    DATASOURCE_REGEXP = re.compile('^datasource.[-\d]+.[a-zA-Z_]+')
    QUERY_REGEXP = re.compile('^queries.[-\d]+.[a-zA-Z_]+$')
    ITEM_REGEXP = re.compile(
        '^queries.[-\d]+.items.[-\d]+.[a-zA-Z_]+$')
    FEATURE_REGEXP = re.compile(
        '^queries.[-\d]+.items.[-\d]+.target_features.[-\d]+.[a-zA-Z_]+$')

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(ImportHandlerResource, self).get(*args, **kwargs)

    def _modify_details_query(self, cursor, params):
        return cursor.options(undefer('data'))

    def _get_download_action(self, **kwargs):
        """
        Downloads importhandler data file.
        """
        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        content = json.dumps(model.data)
        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; \
filename=importhandler-%s.json' % model.name
        return resp

    def put(self, action=None, **kwargs):
        if action:
            return super(ImportHandlerResource, self).put(action, **kwargs)

        obj = self._get_details_query({}, **kwargs)
        if obj is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        self.updated_fields = ['id', ]
        obj = self._update_handler_fields(obj, request.form)
        obj.data = self._get_updated_json_document(obj, request.form)
        obj.import_params = self._get_updated_import_params(obj)

        obj.save()

        def serialize(obj, fields):
            obj_dict = {}
            for field in fields:
                obj_dict[field] = getattr(obj, field)
            return obj_dict

        return self._render({self.OBJECT_NAME: serialize(obj, self.updated_fields)})

    def _get_updated_import_params(self, handler):
        from core.importhandler.importhandler import ExtractionPlan

        try:
            plan = ExtractionPlan(json.dumps(handler.data), is_file=False)
        except ImportHandlerException:
            return []
        return plan.input_params

    def _get_updated_json_document(self, handler, data):
        """
        Updates import handler json document (field data).
        Returns update document dict.

        handler
          Import Handler instance to edit
        data
          PUT data
        """
        from copy import copy
        from datetime import datetime
        from forms import QueryForm, QueryItemForm, TargetFeatureForm, \
            HandlerDataSourceForm
        self.updated = False
        handler_doc = copy(handler.data)

        query_forms = {}
        item_forms = {}
        feature_forms = {}
        datasource_forms = {}
        for key, val in data.iteritems():
            if key == 'target_schema':
                self.updated = True
                handler_doc['target_schema'] = val
                continue

            match = self.DATASOURCE_REGEXP.search(key)
            if match:
                sub_keys = key.split('.')
                ds_num = sub_keys[1]
                if not ds_num in datasource_forms:
                    datasource_forms[ds_num] = HandlerDataSourceForm(
                        handler_doc['datasource'], ds_num)
                field = sub_keys[2]
                datasource_forms[ds_num].append_data(field, val)
                continue

            match = self.QUERY_REGEXP.search(key)
            if match:
                sub_keys = key.split('.')
                query_num = sub_keys[1]
                if not query_num in query_forms:
                    query_forms[query_num] = QueryForm(
                        handler_doc['queries'], query_num)
                field = sub_keys[2]
                query_forms[query_num].append_data(field, val)
                continue

            match = self.ITEM_REGEXP.search(key)
            if match:
                sub_keys = key.split('.')
                query_num = sub_keys[1]
                item_num = sub_keys[3]
                num = (query_num, item_num)
                if not num in item_forms:
                    items = handler_doc['queries'][int(query_num)]['items']
                    item_forms[num] = QueryItemForm(
                        items, item_num)
                field = sub_keys[4]
                item_forms[num].append_data(field, val)
                continue

            match = self.FEATURE_REGEXP.search(key)
            if match:
                sub_keys = key.split('.')
                query_num = sub_keys[1]
                item_num = sub_keys[3]
                feature_num = sub_keys[5]
                num = (query_num, item_num, feature_num)
                if not num in feature_forms:
                    query = handler_doc['queries'][int(query_num)]
                    features = query['items'][int(item_num)]['target_features']
                    feature_forms[num] = TargetFeatureForm(
                        features, feature_num)
                field = sub_keys[6]
                feature_forms[num].append_data(field, val)
                continue

            if key.startswith('remove_'):
                # need to remove query/item/target-feature here
                if 'remove_item' in data:
                    num = int(data.get('num', None))
                    query_num = int(data.get('query_num', None))
                    if num is None or query_num is None:
                        raise ValidationError('num and query_num are required')
                    del handler_doc['queries'][query_num]['items'][num]
                    self.updated = True
                elif 'remove_query' in data:
                    num = int(data.get('num', None))
                    if num is None:
                        raise ValidationError('num is required')
                    del handler_doc['queries'][num]
                    self.updated = True
                elif 'remove_feature' in data:
                    num = int(data.get('num', None))
                    query_num = int(data.get('query_num', None))
                    item_num = int(data.get('item_num', None))
                    if num is None:
                        raise ValidationError('num is required')
                    del handler_doc['queries'][query_num]['items'][item_num]['target_features'][num]
                    self.updated = True

        for form in query_forms.values() + item_forms.values() + \
                feature_forms.values() + datasource_forms.values():
            if form.is_valid():
                form.save()
                self.updated = True
            else:
                raise ValidationError(form.error_messages)

        if self.updated:
            self.updated_fields.append('data')
            self.updated_fields.append('import_params')
            handler_doc['updated_on'] = str(datetime.now())
        return handler_doc

    def _update_handler_fields(self, handler, data):
        """
        Updates import handler simple fields like name

        handler
          Import Handler instance to edit
        data
          PUT data
        """
        from forms import HandlerForm
        form = None
        for key, val in data.iteritems():
            match = self.HANDLER_REGEXP.search(key)
            if match:
                if not form:
                    form = HandlerForm(obj=handler)
                form.append_data(key, val)

        if form is not None:
            if form.is_valid():
                self.updated_fields += form.cleaned_data.keys()
                return form.save()
            else:
                raise ValidationError(form.error_messages)
        return handler

    def _put_run_sql_action(self, **kwargs):
        """
        Run sql query for testing
        """
        from forms import QueryTestForm
        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        form = QueryTestForm(obj={})
        if not form.is_valid():
            return self._render({'error': form.error_messages})

        sql = form.cleaned_data['sql']
        limit = form.cleaned_data['limit']
        params = form.cleaned_data['params']
        datasource_name = form.cleaned_data['datasource']
        try:
            sql = sql % params
        except (KeyError, ValueError):
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        'Wrong query parameters')

        try:
            model.check_sql(sql)
        except Exception as e:
            return odesk_error_response(400, ERR_INVALID_DATA, str(e))

        # Change query LIMIT
        sql = model.build_query(sql, limit=limit)

        try:
            data = list(model.execute_sql_iter(sql, datasource_name))
        except DatabaseError as e:
            return odesk_error_response(400, ERR_INVALID_DATA, str(e))

        columns = []
        if len(data) > 0:
            columns = data[0].keys()

        return self._render({'data': data, 'columns': columns, 'sql': sql})

    def _put_test_handler_action(self, **kwargs):
        """
        Run importing data for testing
        """
        from forms import ImportHandlerTestForm
        from core.importhandler.importhandler import ExtractionPlan,\
            ImportHandler

        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        form = ImportHandlerTestForm(obj={})
        if not form.is_valid():
            return self._render({'error': form.error_messages})

        import_params = form.cleaned_data['params']
        limit = form.cleaned_data['limit']

        # Change limit for all handler queries
        for query in model.data['queries']:
            query['sql'] = model.build_query(query['sql'], limit=limit)

        try:
            handler = json.dumps(model.data)
            plan = ExtractionPlan(handler, is_file=False)
            handler = ImportHandler(plan, import_params)
            content = (json.dumps(row, cls=DecimalEncoder) for row in handler)
            content = '\n'.join(content)
        except Exception as e:
            return odesk_error_response(400, ERR_INVALID_DATA, str(e))

        from api.amazon_utils import AmazonS3Helper
        helper = AmazonS3Helper()
        name = '{!s}.txt'.format(uuid.uuid4())
        helper.save_key_string(name, content)
        return self._render({'url': helper.get_download_url(name, 3600)})

api.add_resource(ImportHandlerResource, '/cloudml/importhandlers/')


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
        ds = self._get_details_query({}, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        url = ds.get_s3_download_url()
        return self._render({self.OBJECT_NAME: ds.id,
                             'url': url})

    def _put_reupload_action(self, **kwargs):
        from api.import_handlers.tasks import upload_dataset
        dataset = self._get_details_query({}, **kwargs)
        if dataset.status == DataSet.STATUS_ERROR:
            dataset.status = DataSet.STATUS_IMPORTING
            dataset.save()
            upload_dataset.delay(dataset.id)
        return self._render({self.OBJECT_NAME: dataset})

    def _put_reimport_action(self, **kwargs):
        from tasks import import_data
        dataset = self._get_details_query({}, **kwargs)
        if dataset.status not in (DataSet.STATUS_IMPORTING,
                                  DataSet.STATUS_UPLOADING):
            dataset.status = DataSet.STATUS_IMPORTING
            dataset.save()
            import_data.delay(dataset_id=dataset.id)

        return self._render({self.OBJECT_NAME: dataset})

api.add_resource(DataSetResource, '/cloudml/importhandlers/\
<regex("[\w\.]*"):import_handler_id>/datasets/')
