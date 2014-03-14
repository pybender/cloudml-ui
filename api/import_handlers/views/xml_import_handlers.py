from api.base.resources import BaseResourceSQL
from api import api
from api.import_handlers.models import XmlImportHandler, XmlInputParameter,\
    XmlDataSource
from api.import_handlers.forms import XmlImportHandlerAddForm, \
    XmlInputParameterForm, XmlDataSourceForm


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
            res['entities'] = get_entity_tree(model)

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
