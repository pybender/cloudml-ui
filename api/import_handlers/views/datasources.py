from api import api
from api.base.resources import BaseResourceSQL
from api.import_handlers.models import PredefinedDataSource
from api.import_handlers.forms import PredefinedDataSourceForm


class PredefinedDataSourceResource(BaseResourceSQL):
    """
    Predefined DataSource API methods
    """
    DEFAULT_FIELDS = ['id', 'name', 'db']
    put_form = post_form = PredefinedDataSourceForm

    @property
    def Model(self):
        return PredefinedDataSource

api.add_resource(PredefinedDataSourceResource, '/cloudml/datasources/')
