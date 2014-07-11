from flask import request
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload, joinedload_all

from api.base.resources import BaseResourceSQL
from api import api
from api.import_handlers.models import XmlImportHandler, XmlInputParameter, \
    XmlEntity, XmlField, XmlDataSource, XmlQuery, XmlScript, XmlSqoop, Predict
from api.import_handlers.forms import XmlImportHandlerAddForm, \
    XmlInputParameterForm, XmlEntityForm, XmlFieldForm, XmlDataSourceForm, \
    XmlQueryForm, XmlScriptForm, XmlImportHandlerEditForm, XmlSqoopForm
from api.servers.forms import ChooseServerForm


class XmlImportHandlerResource(BaseResourceSQL):
    """
    XmlImportHandler API methods
    """
    post_form = XmlImportHandlerAddForm
    put_form = XmlImportHandlerEditForm

    PUT_ACTIONS = ('upload_to_server', )

    @property
    def Model(self):
        return XmlImportHandler

    def _modify_details_query(self, cursor, params):
        show = self._get_show_fields(params)
        if 'predict' in show:
            cursor = cursor.options(
                joinedload_all('predict.models'),
                joinedload('predict.models.positive_label'),
                joinedload('predict.label'),
                joinedload('predict.probability'),
                joinedload('predict.label.predict_model'),
                joinedload('predict.probability.predict_model'))
        return cursor

    def _prepare_model(self, model, params):
        res = super(XmlImportHandlerResource, self)._prepare_model(
            model, params)
        show = self._get_show_fields(params)
        if 'xml' in show:
            res['xml'] = model.get_plan_config()

        if 'entities' in show:
            from ..models import get_entity_tree
            res['entity'] = get_entity_tree(model)

        # if 'predict' in show:
        #     if model.predicts:
        #         predict = model.predict
        #         print predict.models
        #         res['predict'] = predict
        #     else:
        #         res['predict'] = None
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
            cursor = cursor.filter(XmlField.transform.in_(XmlField.TRANSFORM_TYPES))
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

    def _get_details_query(self, params, **kwargs):
        try:
            handler_id = kwargs.pop('import_handler_id')
            return self._build_details_query(params, **kwargs)
        except NoResultFound:
            return None

api.add_resource(XmlSqoopResource, '/cloudml/xml_import_handlers/\
<regex("[\w\.]*"):import_handler_id>/entities/<regex("[\w\.]*"):entity_id>\
/sqoop_imports/')
