import json
import logging
import math
from flask.ext import restful
from flask.ext.restful import reqparse
from sqlalchemy import desc

from api.decorators import authenticate
from api.utils import crossdomain, ERR_NO_SUCH_MODEL, odesk_error_response, \
    ERR_INVALID_METHOD, ERR_INVALID_DATA
from api.serialization import encode_model
from api import app


class NotFound(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors', None)
        super(ValidationError, self).__init__(*args, **kwargs)


class BaseResource(restful.Resource):
    """
    Base class for any API Resource
    """
    ALLOWED_METHODS = ('get', 'post', 'put', 'delete', 'options')
    GET_ACTIONS = ()
    POST_ACTIONS = ()
    PUT_ACTIONS = ()
    ALL_FIELDS_IN_POST = False

    DETAILS_PARAM = '_id'
    OBJECT_NAME = 'model'
    NEED_PAGING = False
    GET_PARAMS = (('show', str), )
    FILTER_PARAMS = ()
    PAGING_PARAMS = (('page', int), ('per_page', int))
    SORT_PARAMS = (('sort_by', str), ('order', str))

    ENABLE_FULLTEXT_SEARCH = True
    FULLTEXT_SEARCH_PARAM_NAME = 'q'

    MESSAGE404 = "Object doesn't exist"
    ORDER_DICT = {'asc': 1, 'desc': -1}
    methods = ('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')
    decorators = [
        crossdomain(origin='*',
                    headers="accept, origin, content-type, X-Auth-Token",
                    methods=['get', 'post', 'put', 'delete', 'options']
                    )]
    method_decorators = [authenticate]

    DEFAULT_FIELDS = ['id', 'name']
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
            return odesk_error_response(404, ERR_NO_SUCH_MODEL, str(exc))
        except ValidationError, exc:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        str(exc), errors=exc.errors)

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
            extra_fields = form.cleaned_data.keys()
        else:
            raise ValidationError(form.error_messages)

        return self._render(self._get_save_response_context(obj, extra_fields=extra_fields),
                            code=200)

    def delete(self, action=None, **kwargs):
        """
        Deletes unused model
        """
        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        self._delete_validataion(model)
        model.delete()
        return '', 204

    def _delete_validataion(self, model):
        pass

    def _list(self, extra_params=(), **kwargs):
        """
        Gets list of models

        GET parameters:
            * show - list of fields to return
        """
        parser_params = tuple(extra_params) + self.GET_PARAMS + tuple(self.FILTER_PARAMS) + \
            self.SORT_PARAMS
        if self.NEED_PAGING:
            parser_params += self.PAGING_PARAMS
        params = self._parse_parameters(parser_params)
        query_fields, show_fields = self._get_fields(params)

        # Removing empty values
        kw = dict([(k, v) for k, v in kwargs.iteritems() if v])
        models = self._get_list_query(params, query_fields, **kw)
        context = {}
        if self.NEED_PAGING:
            context['per_page'] = per_page = params.get('per_page') or 20
            context['page'] = page = params.get('page') or 1
            total, models = self._paginate(models, page, per_page)
            context['total'] = total
            context['pages'] = pages = int(math.ceil(1.0 * total / per_page))
            context['has_prev'] = page > 1
            context['has_next'] = page < pages

        if query_fields != show_fields:
            models = [_filter_model_fields(model, show_fields)
                      for model in models]

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
        query_fields, show_fields = self._get_fields(params)
        model = self._get_details_query(params, query_fields, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        if query_fields != show_fields:
            model = _filter_model_fields(model, show_fields)

        return self._render({self.OBJECT_NAME: model})

    def _get_save_response_context(self, model, extra_fields=[]):
        if not self.ALL_FIELDS_IN_POST:
            model = dict([(field, getattr(model, field, None))
                     for field in list(self.DEFAULT_FIELDS) + extra_fields])
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
        def is_none_or_empty(val):
            return val is None or val == ''

        filter_names = [v[0] for v in self.FILTER_PARAMS]
        return dict([(k, v) for k, v in params.iteritems()
                    if not is_none_or_empty(v) and k in filter_names])

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

    def _get_fields(self, params):
        show = params.get('show', None)
        fields = ['_id'] + show.split(',') if show else ('name', '_id')
        if getattr(self.Model, 'use_autorefs', False):
            query_fields = []
            for field in fields:
                if '.' in field:
                    fieldname = field.split('.')[0]
                    from mongokit.document import R
                    if isinstance(self.Model.structure[fieldname], R):
                        query_fields.append(fieldname)
                        continue
                query_fields.append(field)
            return query_fields, fields
        else:
            return fields, fields

    def _render(self, content, code=200):
        try:
            content = json.dumps(content, default=encode_model)
        except Exception, exc:
            msg = 'Error when dump data: %s' % exc
            logging.error(msg)
            return odesk_error_response(500, ERR_INVALID_DATA, msg)

        return app.response_class(content,
                                  mimetype='application/json'), code


class BaseResourceSQL(BaseResource):
    """
    Base REST resource for SQL models.
    """

    def _get_list_query(self, params, fields, **kwargs):
        filter_params = self._prepare_filter_params(params)
        sort_by = params.get('sort_by', None)
        order = None
        if sort_by:
            order = params.get('order') or 'asc'
            try:
                order = self.ORDER_DICT[order]
            except KeyError:
                raise ValidationError('Invalid order. It could be asc or desc')

        kwargs.update(filter_params)

        # TODO: load only 'fields'
        # cursor = self.Model.query.filter_by(**kwargs)
        cursor = self.__build_query(kwargs)
        print cursor

        if sort_by:
            sort_by = getattr(self.Model, sort_by, None)
            if sort_by:
                if order < 0:
                    sort_by = desc(sort_by)
                cursor = cursor.order_by(sort_by)

        return cursor

    def __build_query(self, filter_params):
        # TODO: What about joins?
        cursor = self.Model.query
        for name, val in filter_params.iteritems():
            cursor = cursor.filter(self.__build_query_item(name, val))
        return cursor

    def __build_query_item(self, name, val):
        if '.' in name:
            keys = name.split('.')
            field = getattr(self.Model, keys[0])
            return getattr(field, keys[1])(val)
        elif '->>' in name:
            return "%s='%s'" % (name, val)
        else:
            return getattr(self.Model, name) == val

    def _paginate(self, cursor, page, per_page=20):
        paginator = cursor.paginate(page, per_page)
        return paginator.total, paginator.items

    def _get_details_query(self, params, fields, **kwargs):
        if '_id' in kwargs:
            kwargs['id'] = kwargs['_id']
            del kwargs['_id']
        model = self.Model.query.filter_by(**kwargs).one()
        return model


def _filter_model_fields(model, show_fields):
    res = {}
    for field in show_fields:
        if '.' in field:
            subfields = field.split('.')
            inner = res
            inner_model = model
            for subfield in subfields:
                from flask.ext.mongokit import Document
                if inner_model and subfield in inner_model:
                    val = getattr(inner_model, subfield)
                    if isinstance(val, Document):
                        if not subfield in inner:
                            inner[subfield] = {}
                    else:
                        inner[subfield] = val
                    inner_model = val
                    inner = inner[subfield]
        else:
            if field in model:
                res[field] = getattr(model, field)
    return res


from api.logs.views import *