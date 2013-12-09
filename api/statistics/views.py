from sqlalchemy import func

from api import api, app
from api.base.resources import BaseResourceSQL
from api.models import Model, Test, DataSet


class StatisticsResource(BaseResourceSQL):
    """ Statistics methods """

    def get(self, action=None):
        return self._render({'statistics': {
            'models': get_stat_by_status(Model),
            'tests': get_stat_by_status(Test),
            'datasets': get_stat_by_status(DataSet),
        }})

api.add_resource(StatisticsResource, '/cloudml/statistics/')


def get_stat_by_status(Cls):
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
