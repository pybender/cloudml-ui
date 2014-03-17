from api.base.resources import BaseResourceSQL
from api import api
from api.import_handlers.models import XmlImportHandler, XmlInputParameter, \
    XmlEntity, XmlField, XmlDataSource, XmlQuery, XmlScript
from api.import_handlers.forms import XmlImportHandlerAddForm, \
    XmlInputParameterForm, XmlEntityForm, XmlFieldForm, XmlDataSourceForm, \
    XmlQueryForm, XmlScriptForm


class XmlImportHandlerResource(BaseResourceSQL):
    """
    XmlImportHandler API methods
    """
    post_form = XmlImportHandlerAddForm

    @property
    def Model(self):
        return XmlImportHandler

    def _prepare_model(self, model, params):
        res = super(XmlImportHandlerResource, self)._prepare_model(
            model, params)
        show = self._get_show_fields(params)
        if 'xml' in show:
            res['xml'] = model.get_plan_config()

        if 'entities' in show:
            from ..models import get_entity_tree
            res['entity'] = get_entity_tree(model)

        return res

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

api.add_resource(
    XmlInputParameterResource,
    '/cloudml/xml_import_handlers/input_parameters/')


class XmlEntityResource(BaseResourceSQL):
    """
    XmlEntity API methods
    """
    put_form = post_form = XmlEntityForm
    Model = XmlEntity

api.add_resource(
    XmlEntityResource,
    '/cloudml/xml_import_handlers/entities/')


class XmlFieldResource(BaseResourceSQL):
    """
    XmlField API methods
    """
    put_form = post_form = XmlFieldForm
    Model = XmlField
    GET_ACTIONS = ('configuration', )

    def _get_configuration_action(self, **kwargs):
        return self._render({'configuration': {
            'types': XmlField.TYPES,
            'transform': XmlField.TRANSFORM_TYPES}})

api.add_resource(
    XmlFieldResource,
    '/cloudml/xml_import_handlers/fields/')


class XmlDataSourceResource(BaseResourceSQL):
    """
    XmlDataSource API methods
    """
    put_form = post_form = XmlDataSourceForm
    Model = XmlDataSource
    GET_ACTIONS = ('configuration', )

    def _get_configuration_action(self, **kwargs):
        from core.xmlimporthandler.importhandler import ExtractionPlan
        conf = ExtractionPlan.get_datasources_config()
        return self._render({'configuration': conf})

api.add_resource(
    XmlDataSourceResource,
    '/cloudml/xml_import_handlers/datasources/')


class XmlQueryResource(BaseResourceSQL):
    """
    XmlQuery API methods
    """
    put_form = post_form = XmlQueryForm
    Model = XmlQuery
    DEFAULT_FIELDS = ['id', 'text', 'target']

api.add_resource(
    XmlQueryResource,
    '/cloudml/xml_import_handlers/queries/')


class XmlScriptResource(BaseResourceSQL):
    """
    XmlScript API methods
    """
    put_form = post_form = XmlScriptForm
    Model = XmlScript

api.add_resource(
    XmlScriptResource,
    '/cloudml/xml_import_handlers/<regex("[\w\.]*"):import_handler_id>/scripts/')
