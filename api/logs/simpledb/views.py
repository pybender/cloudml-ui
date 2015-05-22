from api.base.resources import BaseResource
from models import LogMessage


class LogResource(BaseResource):
    """ Log API methods """
    ALLOWED_METHODS = ('get', )
    FILTER_PARAMS = (('type', str), ('level', str), ('object_id', int))
    NEED_PAGING = True
    DETAILS_PARAM = 'id'
    PAGING_PARAMS = (('next_token', str), ('per_page', int))

    def get(self):
        params = self._get_list_parameters()

        def _get_required(name):
            if name not in params:
                raise ValidationError('%s is required' % name)
            return params[name]

        type_ = _get_required('type')
        object_id = _get_required('object_id')
        next_token = params.get('next_token', None)
        level = params.get('level', None)
        limit = params.get('per_page', 10)
        show = params.get('show', '').split(',')
        res = LogMessage.filter_by_object(
            type_, object_id,
            level, next_token=next_token,
            limit=limit)
        logs = [log.to_dict() for log in res]
        return self._render({'logs': logs, 'next_token': res.next_token})
