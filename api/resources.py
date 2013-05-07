import json
import logging
import math
from flask.ext import restful
from flask.ext.restful import reqparse

from api.utils import crossdomain, ERR_NO_SUCH_MODEL, odesk_error_response, \
    ERR_INVALID_METHOD, ERR_INVALID_DATA
from api.serialization import encode_model
from api import app


class NotFound(Exception):
    pass


class ValidationError(Exception):
    pass


class BaseResource(restful.Resource):
    """
    Base class for any API Resource
    """
    ALLOWED_METHODS = ('get', 'post', 'put', 'delete', 'options')
    GET_ACTIONS = ()
    POST_ACTIONS = ()
    PUT_ACTIONS = ()

    DETAILS_PARAM = 'name'
    OBJECT_NAME = 'model'
    NEED_PAGING = False
    GET_PARAMS = (('show', str), )
    FILTER_PARAMS = ()
    PAGING_PARAMS = (('page', int), )

    MESSAGE404 = "Object doesn't exist"
    decorators = [crossdomain(origin='*',
                              headers="accept, origin, content-type")]

    @property
    def Model(self):
        """
        Returns base DB model of the Resource.
        """
        raise NotImplemented()

    @property
    def list_key(self):
        """
        Returns a key name, when list of results returned.
        """
        return '%ss' % self.OBJECT_NAME

    def dispatch_request(self, *args, **kwargs):
        from flask import request
        method = request.method.lower()
        if not method in self.ALLOWED_METHODS:
            return odesk_error_response(400, ERR_INVALID_METHOD,
                                        '%s is not allowed' % method)
        try:
            return super(BaseResource, self).dispatch_request(*args, **kwargs)
        except NotFound, exc:
            return odesk_error_response(404, ERR_NO_SUCH_MODEL, exc.message)
        except ValidationError, exc:
            return odesk_error_response(400, ERR_INVALID_DATA, exc.message)

    # HTTP Methods

    def get(self, action=None, **kwargs):
        """
        GET model/models.
            * action - specific action for GET method.
                Note: action should be in `GET_ACTIONS` list and
                _get_{{ action }}_action method should be implemented.
            * ... - list of url parameters. For example parent_name and name.
        """
        if action:
            return self._apply_action(action, method='GET', **kwargs)

        if self._is_list_method(**kwargs):
            return self._list(**kwargs)
        else:
            return self._details(**kwargs)

    def post(self, action=None, **kwargs):
        """
        Adds new model
        """
        if action:
            return self._apply_action(action, method='POST', **kwargs)
        parser = self._get_model_parser()
        try:
            params = parser.parse_args() if parser else []
        except Exception, exc:
            if hasattr(exc, 'data') and 'message' in exc.data:
                raise ValidationError(exc.data['message'])
            raise

        self._validate_parameters(params)
        model = self._get_post_model(params, **kwargs)
        self._fill_post_data(model, params, **kwargs)
        return self._render({self.OBJECT_NAME: model._id}, code=201)

    def put(self, action=None, **kwargs):
        """
        Updates new model
        """
        if action:
            return self._apply_action(action, method='PUT', **kwargs)

        parser = self._get_model_parser(method='PUT')
        params = parser.parse_args()

        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        model = self._fill_put_data(model, params, **kwargs)
        return self._render({self.OBJECT_NAME: model._id}, code=200)

    def delete(self, action=None, **kwargs):
        """
        Deletes unused model
        """
        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        model.delete()
        return '', 204

    def _list(self, extra_params=(), **kwargs):
        """
        Gets list of models

        GET parameters:
            * show - list of fields to return
        """
        parser_params = extra_params + self.GET_PARAMS + self.FILTER_PARAMS
        if self.NEED_PAGING:
            parser_params += self.PAGING_PARAMS
        params = self._parse_parameters(parser_params)
        fields = self._get_fields_to_show(params)

        # Removing empty values
        kw = dict([(k, v) for k, v in kwargs.iteritems() if v])
        models = self._get_list_query(params, fields, **kw)
        context = {}
        if self.NEED_PAGING:
            context['per_page'] = per_page = params.get('per_page') or 20
            context['page'] = page = params.get('page') or 1
            total, models = self._paginate(models, page, per_page)
            context['total'] = total
            context['pages'] = pages = int(math.ceil(1.0 * total / per_page))
            context['has_prev'] = page > 1
            context['has_next'] = page < pages

        context.update({self.list_key: models})
        return self._render(context)

    def _paginate(self, models, page, per_page=20):
        total = models.count()
        offset = (page - 1) * per_page
        models = models.skip(offset).limit(per_page)
        return total, models

    def _details(self, extra_params=(), **kwargs):
        """
        GET model by name
        """
        params = self._parse_parameters(extra_params + self.GET_PARAMS)
        fields = self._get_fields_to_show(params)
        model = self._get_details_query(params, fields, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        return self._render({self.OBJECT_NAME: model})

    # Specific actions for GET

    def _get_list_query(self, params, fields, **kwargs):
        filter_params = self._prepare_filter_params(params)
        kwargs.update(filter_params)
        return self.Model.find(kwargs, fields)

    def _prepare_filter_params(self, params):
        filter_names = [v[0] for v in self.FILTER_PARAMS]
        return dict([(k, v) for k, v in params.iteritems()
                    if not v is None and k in filter_names])

    def _get_details_query(self, params, fields, **kwargs):
        model = self.Model.find_one(kwargs, fields)
        return model

    def _get_model_parser(self, **kwargs):
        return None

    # Specific methods for POST

    def _validate_parameters(self, params):
        pass

    def _fill_post_data(self, obj, params, **kwargs):
        raise NotImplemented()

    def _get_post_model(self, params, **kwargs):
        """
        It should be overridden when it's subdocument resource.
        In this case parent model already exist and we need to
        add elements in subdocument.
        """
        return self.Model()

    # Utility methods

    def _apply_action(self, action, method='GET', **kwargs):
        if action in getattr(self, '%s_ACTIONS' % method):
            method_name = "_%s_%s_action" % (method.lower(), action)
            return getattr(self, method_name)(**kwargs)
        else:
            return odesk_error_response(404, ERR_NO_SUCH_MODEL,
                                        "Invalid action \
for %s method: %s" % (method, action))

    def _is_list_method(self, **kwargs):
        name = kwargs.get(self.DETAILS_PARAM)
        return not name

    def _parse_parameters(self, extra_params=()):
        parser = reqparse.RequestParser()
        for name, param_type in extra_params:
            parser.add_argument(name, type=param_type)
        return parser.parse_args()

    def _get_fields_to_show(self, params):
        fields = params.get('show', None)
        return fields.split(',') if fields else ('name', )

    def _render(self, content, code=200):
        try:
            content = json.dumps(content, default=encode_model)
        except Exception, exc:
            msg = 'Error when dump data: %s' % exc
            logging.error(msg)
            return odesk_error_response(500, ERR_INVALID_DATA, msg)

        return app.response_class(content,
                                  mimetype='application/json'), code
