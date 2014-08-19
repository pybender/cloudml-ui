from api.base.resources import BaseResourceMongo
from api import app


class LogResource(BaseResourceMongo):  # pragma: no cover
    """ Log API methods """
    FILTER_PARAMS = (('type', str), ('level', str), ('params.obj', int))
    NEED_PAGING = True
    DETAILS_PARAM = '_id'

    @property
    def Model(self):
        return app.db.LogMessage

    def _prepare_filter_params(self, params):
        params = super(LogResource, self)._prepare_filter_params(params)

        
        if 'level' in params:
            all_levels = ['CRITICAL', 'ERROR', 'WARN', 'WARNING',
                          'INFO', 'DEBUG', 'NOTSET']
            if params['level'] in all_levels:
                idx = all_levels.index(params['level'])
                levels = [l for i, l in enumerate(all_levels) if i <= idx]
                params['level'] = {'$in': levels}
            else:
                del params['level']

        return params
