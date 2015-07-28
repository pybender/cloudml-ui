import re

from api import api
from api.base.resources import BaseResourceSQL
from api.import_handlers.models import PredefinedDataSource
from api.import_handlers.forms import PredefinedDataSourceForm


class PredefinedDataSourceResource(BaseResourceSQL):
    """
    Predefined DataSource API methods
    """
    DEFAULT_FIELDS = ['id', 'name', 'db']
    Model = PredefinedDataSource
    put_form = post_form = PredefinedDataSourceForm

    def _get_list_query(self, params, **kwargs):
        fields = self._get_show_fields(params)
        datasources = super(
            PredefinedDataSourceResource, self)._get_list_query(
                params, **kwargs)
        if 'db' not in fields:
            return datasources

        # replacing the password from the conn string with stars
        result = []
        for ds in datasources:
            item = dict([(field, getattr(ds, field))
                         for field in fields])
            if not ds.can_edit:
                item['db'] = ds.safe_db
            result.append(item)
        return result

    def _get_details_query(self, params, **kwargs):
        ds = super(
            PredefinedDataSourceResource, self)._get_details_query(
                params, **kwargs)
        if not params:
            return ds

        fields = self._get_show_fields(params)
        if 'db' not in fields:
            return ds

        item = dict([(field, getattr(ds, field))
                     for field in fields])
        if not ds.can_edit:
            item['db'] = ds.safe_db
        return item

api.add_resource(PredefinedDataSourceResource, '/cloudml/datasources/')
