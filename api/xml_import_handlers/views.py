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

api.add_resource(XmlImportHandlerResource, '/cloudml/xml_import_handlers/')
