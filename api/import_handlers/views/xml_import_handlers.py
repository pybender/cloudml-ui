import re

from flask import request
from psycopg2._psycopg import DatabaseError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload, joinedload_all, undefer

from api.base.resources import BaseResourceSQL, NotFound, \
    odesk_error_response, ERR_INVALID_DATA
from api import api
from api.import_handlers.models import XmlImportHandler, XmlInputParameter, \
    XmlEntity, XmlField, XmlDataSource, XmlQuery, XmlScript, XmlSqoop, \
    Predict, PredictModel, PredictModelWeight, PredictResultLabel, \
    PredictResultProbability
from api.import_handlers.forms import XmlImportHandlerAddForm, \
    XmlInputParameterForm, XmlEntityForm, XmlFieldForm, XmlDataSourceForm, \
    XmlQueryForm, XmlScriptForm, XmlImportHandlerEditForm, XmlSqoopForm, \
    PredictModelForm, PredictModelWeightForm, PredictResultLabelForm, \
    PredictResultProbabilityForm, XmlImportHandlerUpdateXmlForm
from api.servers.forms import ChooseServerForm


class XmlImportHandlerResource(BaseResourceSQL):
    """
    XmlImportHandler API methods
    """
    post_form = XmlImportHandlerAddForm
    put_form = XmlImportHandlerEditForm

    NEED_PAGING = True
    PUT_ACTIONS = ('upload_to_server', 'run_sql', 'update_xml')
    POST_ACTIONS = ('clone', )
    FILTER_PARAMS = (('created_by', str), ('updated_by_id', int),
                     ('updated_by', str), ('name', str))

    @property
    def Model(self):
        return XmlImportHandler

    def _modify_details_query(self, cursor, params):
        show = self._get_show_fields(params)
        if 'predict' in show:
            cursor = cursor.options(
                joinedload_all('predict.models'),
                joinedload('predict.label'),
                joinedload('predict.probability'),
                joinedload('predict.models.predict_model_weights'),
                joinedload('predict.label.predict_model'),
                joinedload('predict.probability.predict_model'))
        if 'xml_data_sources' in show:
            cursor = cursor.options(
                undefer('xml_data_sources.params'))
        return cursor

    def _set_list_query_opts(self, cursor, params):
        # if 'tag' in params and params['tag']:
        #     cursor = cursor.filter(Model.tags.any(Tag.text == params['tag']))
        name = params.pop('name', None)
        if name:
            cursor = cursor.filter(
                XmlImportHandler.name.ilike('%{0}%'.format(name)))
        created_by = params.pop('created_by', None)
        if created_by:
            cursor = cursor.filter(
                XmlImportHandler.created_by.has(uid=created_by))
        updated_by = params.pop('updated_by', None)
        if updated_by:
            cursor = cursor.filter(
                XmlImportHandler.updated_by.has(uid=updated_by))
        return cursor

    def _prepare_model(self, handler, params):
        res = super(XmlImportHandlerResource, self)._prepare_model(
            handler, params)
        show = self._get_show_fields(params)
        if 'xml' in show:
            res['xml'] = handler.get_plan_config(secure=handler.can_edit)

        if 'entities' in show:
            from ..models import get_entity_tree
            res['entity'] = get_entity_tree(handler)

        if 'xml_data_sources' in show and not handler.can_edit:
            for ds in handler.xml_data_sources:
                ds.params = None

        return res

    def _put_upload_to_server_action(self, **kwargs):
        from api.servers.tasks import upload_import_handler_to_server

        handler = self._get_details_query(None, **kwargs)

        form = ChooseServerForm(obj=handler)
        if form.is_valid():
            server = form.cleaned_data['server']
            upload_import_handler_to_server.delay(server.id,
                                                  XmlImportHandler.TYPE,
                                                  handler.id,
                                                  request.user.id)

            return self._render({
                self.OBJECT_NAME: handler,
                'status': 'Import Handler "{0}" will be uploaded to server'.format(
                    handler.name
                )
            })

    # TODO: nader20140721: we need to refactor this one with the same one
    # in `api.import_handlers.views.json_import_handlers.py`
    def _put_run_sql_action(self, **kwargs):
        """
        Run sql query for testing
        """
        from api.import_handlers.forms import QueryTestForm
        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        form = QueryTestForm(obj={})
        if not form.is_valid():
            return self._render({'error': form.error_messages})

        sql = form.cleaned_data['sql']
        limit = form.cleaned_data['limit']
        params = form.cleaned_data.get('params', {})
        datasource_name = form.cleaned_data['datasource']
        try:
            sql = re.sub('#{(\w+)}', '%(\\1)s', sql)
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

    def _post_clone_action(self, **kwargs):
        from datetime import datetime
        handler = self._get_details_query(None, **kwargs)
        name = "{0} clone: {1}".format(
            handler.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        new_handler = XmlImportHandler(name=name)
        try:
            new_handler.data = handler.data
        except Exception, exc:
            return odesk_error_response(
                400, ERR_INVALID_DATA, str(exc))
        new_handler.save()
        return self._render({
            self.OBJECT_NAME: new_handler,
            'status': 'New import handler "{0}" created'.format(
                new_handler.name
            )
        }, code=201)

    def _put_update_xml_action(self, **kwargs):
        handler = self._get_details_query(None, **kwargs)

        form = XmlImportHandlerUpdateXmlForm(obj={})
        if not form.is_valid():
            return self._render({'error': form.error_messages})

        try:
            for e in XmlEntity.query.filter_by(import_handler=handler).all():
                e.delete()
            handler.data = form.cleaned_data['data']
        except Exception, exc:
            return odesk_error_response(400, ERR_INVALID_DATA, str(exc))
        handler.save()

        return self._render({
            self.OBJECT_NAME: handler,
            'status': 'Import Handler "{0}" has been updated'.format(
                handler.name)
        })


api.add_resource(
    XmlImportHandlerResource, '/cloudml/xml_import_handlers/')


class XmlInputParameterResource(BaseResourceSQL):
    """
    XmlInputParameter API methods
    """
    put_form = post_form = XmlInputParameterForm
    Model = XmlInputParameter
    GET_ACTIONS = ('configuration', )

    def _get_configuration_action(self, **kwargs):
        return self._render({'configuration': {
            'types': XmlInputParameter.TYPES}})

api.add_resource(XmlInputParameterResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/input_parameters/')


class XmlEntityResource(BaseResourceSQL):
    """
    XmlEntity API methods
    """
    put_form = post_form = XmlEntityForm
    Model = XmlEntity

api.add_resource(
    XmlEntityResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/entities/')


class XmlFieldResource(BaseResourceSQL):
    """
    XmlField API methods
    """
    put_form = post_form = XmlFieldForm
    Model = XmlField
    GET_ACTIONS = ('configuration', )
    FILTER_PARAMS = (('transformed', str),)

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

    def _set_list_query_opts(self, cursor, params):
        if 'transformed' in params and params['transformed']:
            cursor = cursor.filter(
                XmlField.transform.in_(XmlField.TRANSFORM_TYPES))
        return cursor

    def _get_configuration_action(self, **kwargs):
        return self._render({'configuration': {
            'types': XmlField.TYPES,
            'transform': XmlField.TRANSFORM_TYPES}})

api.add_resource(XmlFieldResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/entities/<regex("[\w\.]*"):entity_id>\
/fields/')


class XmlDataSourceResource(BaseResourceSQL):
    """
    XmlDataSource API methods
    """
    put_form = post_form = XmlDataSourceForm
    Model = XmlDataSource
    GET_ACTIONS = ('configuration', )
    FILTER_PARAMS = (('type', str), )

    def _get_configuration_action(self, **kwargs):
        from core.xmlimporthandler.importhandler import ExtractionPlan
        conf = ExtractionPlan.get_datasources_config()
        return self._render({'configuration': conf})

api.add_resource(
    XmlDataSourceResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/datasources/')


class XmlQueryResource(BaseResourceSQL):
    """
    XmlQuery API methods
    """
    put_form = post_form = XmlQueryForm
    Model = XmlQuery
    DEFAULT_FIELDS = ['id', 'text', 'target']

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            entity_id = kwargs.pop('entity_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

api.add_resource(
    XmlQueryResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/entities/\
<regex("[\w\.]*"):entity_id>/queries/')


class XmlScriptResource(BaseResourceSQL):
    """
    XmlScript API methods
    """
    put_form = post_form = XmlScriptForm
    Model = XmlScript

api.add_resource(
    XmlScriptResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/scripts/')


class XmlSqoopResource(BaseResourceSQL):
    """
    XmlSqoop API methods
    """
    put_form = post_form = XmlSqoopForm
    Model = XmlSqoop
    PUT_ACTIONS = ('pig_fields', )

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

    def _put_pig_fields_action(self, **kwargs):
        from utils import SCHEMA_INFO_FIELDS, PIG_TEMPLATE, construct_pig_sample
        sqoop = self._get_details_query({}, **kwargs)
        if sqoop is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        handler = XmlImportHandler.query.get(kwargs.get('import_handler_id'))
        if handler is None:
            raise NotFound('Import Handler not found')

        from ..forms import LoadPigFieldsForm
        form = LoadPigFieldsForm(obj={})
        if form.is_valid():
            params = form.cleaned_data.get('params')
            datasource = sqoop.datasource.core_datasource
            sql = """{0} select * from {1} limit 1;
    select {2} from INFORMATION_SCHEMA.COLUMNS where table_name = '{1}';
            """.format(sqoop.text.strip(';'), sqoop.table,
                       ','.join(SCHEMA_INFO_FIELDS))
            if params:
                try:
                    sql = re.sub('#{(\w+)}', '%(\\1)s', sql)
                    sql = sql % params
                except (KeyError, ValueError):
                    return odesk_error_response(
                        400, ERR_INVALID_DATA, 'Wrong query parameters')
            try:
                iterator = datasource._get_iter(sql)
                fields_data = [{key: opt[i] for i, key in enumerate(SCHEMA_INFO_FIELDS)} \
                           for opt in iterator]
            except Exception, exc:
                msg = "Can't execute the query: {0}. Error: {1}".format(sql, exc)
                return odesk_error_response(400, 400, msg)

            fields_str = construct_pig_sample(fields_data)
            return self._render({
                'fields': fields_data,
                'sample': PIG_TEMPLATE.format(fields_str),
                'sql': sql})

api.add_resource(XmlSqoopResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/entities/<regex("[\w\.]*"):entity_id>\
/sqoop_imports/')


class PredictModelResource(BaseResourceSQL):
    """
    Predict section of XML import handler API methods
    """
    put_form = post_form = PredictModelForm
    Model = PredictModel

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

    def _get_list_query(self, params, **kwargs):
        handler = self._get_handler(kwargs.pop('import_handler_id'))
        cursor = super(PredictModelResource, self)._get_list_query(params, **kwargs)
        return cursor.filter(
            PredictModel.predict_section.any(id=handler.predict.id))

    def _get_handler(self, handler_id):
        if handler_id is None:
            raise ValidationError('Please specify import handler')

        handler = XmlImportHandler.query.get(handler_id)
        if handler is None:
            raise NotFound()
        return handler

api.add_resource(
    PredictModelResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/predict_models/')


class PredictModelWeightResource(BaseResourceSQL):
    """
    Predict section of XML import handler API methods
    """
    put_form = post_form = PredictModelWeightForm
    Model = PredictModelWeight

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

    def _get_list_query(self, params, **kwargs):
        handler = self._get_handler(kwargs.pop('import_handler_id'))
        return super(PredictModelWeightResource, self)._get_list_query(params, **kwargs)

    def _get_handler(self, handler_id):
        if handler_id is None:
            raise ValidationError('Please specify import handler')

        handler = XmlImportHandler.query.get(handler_id)
        if handler is None:
            raise NotFound()
        return handler

api.add_resource(
    PredictModelWeightResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/predict_models/\
<regex("[\w\.]*"):predict_model_id>/weights/')


class PredictResultLabelResource(BaseResourceSQL):
    """
    Predict section of XML import handler API methods
    """
    put_form = post_form = PredictResultLabelForm
    Model = PredictResultLabel

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

    def _get_list_query(self, params, **kwargs):
        handler = self._get_handler(kwargs.pop('import_handler_id'))
        cursor = super(PredictModelResource, self)._get_list_query(params, **kwargs)
        return cursor.filter(
            PredictModel.predict_section.any(id=handler.predict.id))

    def _get_handler(self, handler_id):
        if handler_id is None:
            raise ValidationError('Please specify import handler')

        handler = XmlImportHandler.query.get(handler_id)
        if handler is None:
            raise NotFound()
        return handler

api.add_resource(
    PredictResultLabelResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/predict_labels/')


class PredictResultProbabilityResource(BaseResourceSQL):
    """
    Predict section of XML import handler API methods
    """
    put_form = post_form = PredictResultProbabilityForm
    Model = PredictResultProbability

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

    def _get_list_query(self, params, **kwargs):
        handler = self._get_handler(kwargs.pop('import_handler_id'))
        cursor = super(PredictModelResource, self)._get_list_query(params, **kwargs)
        return cursor.filter(
            PredictModel.predict_section.any(id=handler.predict.id))

    def _get_handler(self, handler_id):
        if handler_id is None:
            raise ValidationError('Please specify import handler')

        handler = XmlImportHandler.query.get(handler_id)
        if handler is None:
            raise NotFound()
        return handler

api.add_resource(
    PredictResultProbabilityResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/predict_probabilities/')
