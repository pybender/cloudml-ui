from api.base.resources import BaseResourceSQL
from api import api
from models import XmlImportHandler
from forms import XmlImportHandlerAddForm


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
        if 'entities' in self._get_show_fields(params):
            print "TODO"
        return res
        # #
        # return self._prepare_model_any(model, params)

api.add_resource(XmlImportHandlerResource, '/cloudml/xml_import_handlers/')
