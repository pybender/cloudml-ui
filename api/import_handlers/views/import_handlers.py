from api.base.resources import BaseResourceSQL
from api.import_handlers.models import ImportHandler, XmlImportHandler
from api import api


class ImportHandlerResourceForAnyType(BaseResourceSQL):
    """
    Methods for working for any type of import handler: json and xml.
    """
    OBJECT_NAME = 'import_handler'

    def _get_list_query(self, params, **kwargs):
        from sqlalchemy.sql import literal_column
        fields = self._get_show_fields(params)
        qry_json = self.defer_fields(
            ImportHandler,
            ImportHandler.query,
            fields).filter_by(**kwargs)
        qry_xml = self.defer_fields(
            XmlImportHandler,
            XmlImportHandler.query,
            fields).filter_by(**kwargs)
        return qry_json.all() + qry_xml.all()

api.add_resource(
    ImportHandlerResourceForAnyType, '/cloudml/any_importhandlers/')
