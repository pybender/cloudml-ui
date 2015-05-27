"""
This module represents resource that returns statistical info
about all models, tests, etc.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from sqlalchemy import func

from api import api, app
from api.base.resources import BaseResourceSQL
from api.ml_models.models import Model
from api.model_tests.models import TestResult
from api.import_handlers.models import DataSet


class StatisticsResource(BaseResourceSQL):
    """ Statistics methods """

    def get(self, action=None):
        return self._render({'statistics': {
            'models': get_stat_by_status(Model),
            'tests': get_stat_by_status(TestResult),
            'datasets': get_stat_by_status(DataSet),
        }})

api.add_resource(StatisticsResource, '/cloudml/statistics/')


def get_stat_by_status(Cls):
    """
    Returns count of objects by status.

    Cls: sqlalchemy model class (type definition)
        Model, which objects we need to calculate.

    Returns dict like:
    {
        {"count": 10},
        {"data": {
            "status1": {"count": 2},
            "status2": {"count": 3},
            ...
        }
    }
    """
    query = app.sql_db.session.query
    models_by_status = {}
    models_count = 0
    models_query = query(
        Cls.status, func.count(Cls.status)).group_by(Cls.status)
    for item in models_query:
        count = item[1]
        status = item[0]
        models_count += count
        models_by_status[status] = {'count': count}
    return {'count': models_count, 'data': models_by_status}
