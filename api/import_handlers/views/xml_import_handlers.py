from api.base.resources import BaseResourceSQL
from api import api
from api.import_handlers.models import XmlImportHandler
from api.import_handlers.forms import XmlImportHandlerAddForm


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
            res['xml'] = model.to_xml()

        if 'entities' in show:
            from api.xml_import_handlers.models import get_entity_tree
            res['entities'] = get_entity_tree(model)

        return res

api.add_resource(XmlImportHandlerResource, '/cloudml/xml_import_handlers/')
