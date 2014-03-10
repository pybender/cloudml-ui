from api.base.resources import BaseResourceSQL
from api import api
from api.import_handlers.models import XmlImportHandler, ImportHandler


class ImportHandlerSelectorResource(BaseResourceSQL):
    ALLOWED_METHODS = ('get', )

    def get(self, action=None, **kwargs):
        import_handlers = []

        def fill_import_handlers(cls):
            for h in cls.query.all():
                import_handlers.append({'name': h.name,
                                        'id': "%s_%s" % (h.id, h.TYPE)})

        fill_import_handlers(ImportHandler)
        fill_import_handlers(XmlImportHandler)

        return self._render({'import_handlers': import_handlers})

api.add_resource(
    ImportHandlerSelectorResource, '/cloudml/import_handler_selector/')
