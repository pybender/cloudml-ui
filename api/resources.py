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

    DETAILS_PARAM = '_id'
    OBJECT_NAME = 'model'
    NEED_PAGING = False
    GET_PARAMS = (('show', str), )
    FILTER_PARAMS = ()
    PAGING_PARAMS = (('page', int), )
    SORT_PARAMS = (('sort_by', str), ('order', str))

    ENABLE_FULLTEXT_SEARCH = True
    FULLTEXT_SEARCH_PARAM_NAME = 'q'

    MESSAGE404 = "Object doesn't exist"
    ORDER_DICT = {'asc': 1, 'desc': -1}
    decorators = [crossdomain(origin='*',
                              headers="accept, origin, content-type")]

    DEFAULT_FIELDS = None
    is_fulltext_search = False

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

        form = self.post_form(Model=self.Model, **kwargs)
        if form.is_valid():
            obj = form.save()
        else:
            raise ValidationError(form.error_messages)

        return self._render(self._get_save_response_context(obj),
                            code=201)

    def put(self, action=None, **kwargs):
        """
        Updates new model
        """
        if action:
            return self._apply_action(action, method='PUT', **kwargs)

        obj = self._get_details_query(None, None, **kwargs)
        if obj is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        form = self.put_form(obj=obj)
        if form.is_valid():
            obj = form.save()
        else:
            raise ValidationError(form.error_messages)

        return self._render(self._get_save_response_context(obj),
                            code=200)

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
        parser_params = extra_params + self.GET_PARAMS + self.FILTER_PARAMS +\
            self.SORT_PARAMS
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
        # TODO: Watch https://jira.mongodb.org/browse/SERVER-9063
        # and simplify code
        if self.is_fulltext_search:
            total = len(models)
            offset = (page - 1) * per_page
            models = models[offset:page * per_page]
        else:
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

    def _get_save_response_context(self, model):
        if self.DEFAULT_FIELDS:
            model = dict([(field, getattr(model, field))
                         for field in self.DEFAULT_FIELDS])
        return {self.OBJECT_NAME: model}

    # Specific actions for GET

    def _get_list_query(self, params, fields, **kwargs):
        filter_params = self._prepare_filter_params(params)
        sort_by = params.get('sort_by', None)
        if sort_by:
            order = params.get('order') or 'asc'
            try:
                order = self.ORDER_DICT[order]
            except KeyError:
                raise ValidationError('Invalid order. It could be asc or desc')

        if self.ENABLE_FULLTEXT_SEARCH and \
                self.FULLTEXT_SEARCH_PARAM_NAME in filter_params and \
                filter_params[self.FULLTEXT_SEARCH_PARAM_NAME]:
            # Run full text search
            # NOTE: it's betta in mongo now.
            search = filter_params[self.FULLTEXT_SEARCH_PARAM_NAME]
            show = dict([(field, 1) for field in fields])
            del filter_params[self.FULLTEXT_SEARCH_PARAM_NAME]
            kwargs.update(filter_params)
            # NOTE: The text command matches on the complete stemmed word
            res = app.db.command("text", "weights", search=search,
                                 project=show, filter=kwargs,
                                 limit=1000)
            res = [result['obj'] for result in res['results']]
            if sort_by:
                res.sort(key=lambda a: a[sort_by])
                if order == -1:
                    res.reverse()
            self.is_fulltext_search = True
            return res
        else:
            if self.FULLTEXT_SEARCH_PARAM_NAME in filter_params:
                del filter_params[self.FULLTEXT_SEARCH_PARAM_NAME]

            kwargs.update(filter_params)
            cursor = self.Model.find(kwargs, fields)
            if sort_by:
                cursor.sort(sort_by, order)
            return cursor

    def _prepare_filter_params(self, params):
        filter_names = [v[0] for v in self.FILTER_PARAMS]
        return dict([(k, v) for k, v in params.iteritems()
                    if not v is None and k in filter_names])

    def _get_details_query(self, params, fields, **kwargs):
        if '_id' in kwargs:
            from bson.objectid import ObjectId
            kwargs['_id'] = ObjectId(kwargs['_id'])
        model = self.Model.find_one(kwargs, fields)
        return model

    def _get_model_parser(self, **kwargs):
        return None

    # Specific methods for POST
    @property
    def post_form(self):
        raise NotImplemented()

    def _validate_parameters(self, params):
        pass

    def _fill_post_data(self, obj, params, **kwargs):
        raise NotImplemented()

    # Specific methods for POST

    @property
    def put_form(self):
        raise NotImplemented()

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
