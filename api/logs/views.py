from api import api
from api.resources import BaseResourceSQL
from models import LogMessage


class LogResource(BaseResourceSQL):
    """
    Log API methods
    """
    FILTER_PARAMS = (('type', str),
                     ('level', str),
                     ("params.obj", str))
    MESSAGE404 = "Log Message doesn't exist"
    OBJECT_NAME = 'log'
    NEED_PAGING = True
    ALLOWED_METHODS = ('get', )

    @property
    def Model(self):
        return LogMessage

    def _prepare_filter_params(self, params):
        params = super(LogResource, self)._prepare_filter_params(params)

        if 'level' in params:  # let's include all logs with lower level
            if params['level'] in LogMessage.LEVELS_LIST:
                idx = LogMessage.LEVELS_LIST.index(params['level'])
                levels = [l for i, l in
                          enumerate(LogMessage.LEVELS_LIST) if i <= idx]
                params['level.in_'] = levels
            del params['level']

        if 'params.obj' in params:
            params["params->>'obj'"] = params['params.obj']
            del params['params.obj']

        return params

api.add_resource(LogResource, '/cloudml/logs/')
