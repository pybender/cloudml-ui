from sqlalchemy.orm import undefer, joinedload_all, joinedload

from api.base.resources import BaseResourceSQL
from api import api
from models import XmlImportHandler, Field, Entity
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
            def load_ent(parent=None):
                return Entity.query\
                    .options(
                        joinedload_all(Entity.fields),
                        joinedload(Entity.datasource)).filter_by(
                            import_handler=model,
                            entity=parent)

            def new_ent(entity):
                res = {'entity': entity, 'entities': {}}
                for sub_ent in load_ent(entity):
                    res['entities'][sub_ent.name] = new_ent(sub_ent)
                return res

            entity = load_ent().one()
            res['entities'] = {entity.name: new_ent(entity)}

        return res

api.add_resource(XmlImportHandlerResource, '/cloudml/xml_import_handlers/')
