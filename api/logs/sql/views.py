from api import api
from api.base.resources import BaseResourceSQL
from models import LogMessage


class LogSqlResource(BaseResourceSQL):
    """ Log API methods """
    FILTER_PARAMS = (('type', str),
                     ('level', str),
                     ("params.obj", str))
    NEED_PAGING = True
    ALLOWED_METHODS = ('get', )

    Model = LogMessage

    def _prepare_filter_params(self, params):
        params = super(LogSqlResource, self)._prepare_filter_params(params)

        if 'level' in params:  # let's include all logs with lower level
            if params['level'] in LogMessage.LEVELS_LIST:
                idx = LogMessage.LEVELS_LIST.index(params['level'])
                levels = [l for i, l in
                          enumerate(LogMessage.LEVELS_LIST) if i <= idx]
                params['level.in_'] = levels
            del params['level']

        if 'params.obj' in params:
            params["params->>obj"] = params['params.obj']
            del params['params.obj']

        return params


# It's for tests only
api.add_resource(LogSqlResource, '/cloudml/sql_logs/')
