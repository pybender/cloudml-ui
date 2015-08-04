"""
Base resource classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import re
import logging
import math
from flask.ext import restful
from flask.views import MethodViewType
from flask.ext.restful import reqparse
from sqlalchemy import desc
from sqlalchemy.orm import exc as orm_exc, undefer, defer, \
    joinedload_all, properties

from .decorators import authenticate
from .utils import crossdomain, ERR_NO_SUCH_MODEL, odesk_error_response, \
    ERR_INVALID_METHOD, ERR_INVALID_DATA
from serialization import encode_model
from api import app
from .exceptions import NotFound, ValidationError


__all__ = ('BaseResource', 'BaseResourceSQL')


class ResourceMeta(MethodViewType):
    def __new__(meta, name, bases, attrs):
        from ..utils import convert_name
        obj_name = name.replace('Resource', '')
        attrs['OBJECT_NAME'] = convert_name(obj_name)
        attrs['OBJECT_NAME_TEXT'] = convert_name(obj_name, to_text=True)
        attrs['MESSAGE404'] = "%s doesn't exist" % attrs['OBJECT_NAME_TEXT']
        return super(ResourceMeta, meta).__new__(meta, name, bases, attrs)


class BaseResource(restful.Resource):
    """
    Base class for any API Resource
    """
    __metaclass__ = ResourceMeta

    # Methods
    ALLOWED_METHODS = ('get', 'post', 'put', 'delete', 'options')
    GET_ACTIONS = ()
    POST_ACTIONS = ()
    PUT_ACTIONS = ()
    ALL_FIELDS_IN_POST = False  # TODO:

    # Model specific parameters
    Model = None
    DETAILS_PARAM = 'id'
    DEFAULT_FIELDS = [DETAILS_PARAM, 'name']

    # Quering
    NEED_PAGING = False
    GET_PARAMS = (('show', str), )
    FILTER_PARAMS = ()
    PAGING_PARAMS = (('page', int), ('per_page', int))
    SORT_PARAMS = (('sort_by', str), ('order', str))
    POST_PARAMS = ()
    PUT_PARAMS = ()

    ENABLE_FULLTEXT_SEARCH = True
    FULLTEXT_SEARCH_PARAM_NAME = 'q'

    ORDER_DICT = {'asc': 1, 'desc': -1}

    # Forms
    post_form = None
    put_form = None

    methods = ('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')
    decorators = [
        crossdomain(origin='*',
                    headers="accept, origin, content-type, X-Auth-Token",
                    methods=['get', 'post', 'put', 'delete', 'options']
                    )]
    method_decorators = [authenticate]

    is_fulltext_search = False

    def dispatch_request(self, *args, **kwargs):
        from flask import request
        method = request.method.lower()
        if method not in self.ALLOWED_METHODS:
            return odesk_error_response(400, ERR_INVALID_METHOD,
                                        '%s is not allowed' % method)
        try:
            return super(BaseResource, self).dispatch_request(*args, **kwargs)
        except NotFound, exc:
            return odesk_error_response(404, ERR_NO_SUCH_MODEL, str(exc))
        except ValidationError, exc:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        str(exc), errors=exc.errors)
        except AssertionError, exc:
            return odesk_error_response(400, ERR_INVALID_DATA,
                                        str(exc), errors=exc.message)

    def _apply_action(self, action, method='GET', **kwargs):
        if action in getattr(self, '%s_ACTIONS' % method):
            method_name = "_%s_%s_action" % (method.lower(), action)
            return getattr(self, method_name)(**kwargs)
        else:
            return odesk_error_response(
                404, ERR_NO_SUCH_MODEL,
                "Invalid action for %s method: %s" % (method, action))

    # HTTP Methods

    # ===== GET ======

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

    # ==== List specific ====

    def _list(self, extra_params=(), **kwargs):
        """
        Gets list of models

        GET parameters:
            * show - list of fields to return
        """
        params = self._get_list_parameters(extra_params)

        # Removing empty values
        kw = dict([(k, v) for k, v in kwargs.iteritems() if v])
        models = self._get_list_query(params, **kw)
        context = self._get_model_list_context(models, params)
        return self._render(context)

    def _get_model_list_context(self, models, params):
        """ Returns models context """
        context = dict()
        if self.NEED_PAGING:
            context['per_page'] = per_page = params.get('per_page') or 20
            context['page'] = page = params.get('page') or 1
            total, models = self._paginate(models, page, per_page)
            context['total'] = total
            context['pages'] = pages = int(math.ceil(1.0 * total / per_page))
            context['has_prev'] = page > 1
            context['has_next'] = page < pages

        models = self._prepare_model_list(models, params)

        context.update({self.list_key: models})
        return context

    @property
    def list_key(self):
        """ Returns a key name, when list of results returned. """
        return '%ss' % self.OBJECT_NAME

    def _get_list_query(self, params, **kwargs):
        """
        Returns list of models

            * params - parsed GET parameters
            * **kwargs - data from URI
        """
        raise NotImplemented()

    def _paginate(self, models, page, per_page=20):
        raise NotImplemented()

    def _prepare_model_list(self, models, params):
        return models

    def _get_list_parameters(self, extra_params):
        parser_params = tuple(extra_params) + self.GET_PARAMS \
            + self.FILTER_PARAMS + self.SORT_PARAMS
        if self.NEED_PAGING:
            parser_params += self.PAGING_PARAMS
        return self._parse_parameters(parser_params)

    # ==== Details specific ====

    def _details(self, extra_params=(), **kwargs):
        """
        GET model by name
        """
        params = self._get_details_parameters(extra_params)

        model = self._get_details_query(params, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        model = self._prepare_model(model, params)

        return self._render({self.OBJECT_NAME: model})

    def _prepare_model(self, model, params):
        return self._prepare_model_any(model, params)

    def _get_details_query(self, params, **kwargs):
        raise NotImplemented()

    def _get_details_parameters(self, extra_params):
        return self._parse_parameters(extra_params + self.GET_PARAMS)

    # ==== POST ====

    def post(self, action=None, **kwargs):
        """ Adds new model """
        if action:
            return self._apply_action(action, method='POST', **kwargs)

        params = self._parse_parameters(self.POST_PARAMS)

        if self.post_form is None:
            raise ValueError('Specify post form')
        form = self.post_form(Model=self.Model, **kwargs)
        if form.is_valid():
            model = form.save()
        else:
            raise ValidationError(form.error_messages)

        model = self._prepare_new_model(model, params)

        return self._render({self.OBJECT_NAME: model}, code=201)

    def _prepare_new_model(self, model, params):
        return self._prepare_model(model, params)

    # ==== PUT ====

    def put(self, action=None, **kwargs):
        """ Updates new model """
        if action:
            return self._apply_action(action, method='PUT', **kwargs)

        params = self._parse_parameters(self.PUT_PARAMS)

        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        if not model.can_edit:
            return odesk_error_response(
                401, 401, 'You haven\'t permissions to edit')

        if self.put_form is None:
            raise ValueError('Specify put form')

        form = self.put_form(obj=model, **kwargs)
        if form.is_valid():
            model = form.save()
        else:
            raise ValidationError(form.error_messages)

        model = self._prepare_updated_model(model, params)

        return self._render({self.OBJECT_NAME: model}, code=200)

    def _prepare_updated_model(self, model, params):
        return self._prepare_model(model, params)

    # ==== DELETE ====

    def delete(self, action=None, **kwargs):
        """ Deletes unused model """
        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        if not model.can_delete:
            return odesk_error_response(
                401, 401, 'You haven\'t permissions to delete')
        self._delete_validataion(model)
        model.delete()
        return '', 204

    def _delete_validataion(self, model):
        pass

    # ==== Utility methods ====
    def _prepare_model_any(self, model, params):
        return model

    def _is_list_method(self, **kwargs):
        name = kwargs.get(self.DETAILS_PARAM)
        return not name

    def _get_show_fields(self, params):
        fields = params.get('show', None) if params else None
        if fields:
            res_fields = fields.split(',')
        else:
            res_fields = self.DEFAULT_FIELDS
        if 'id' not in res_fields:
            res_fields.insert(0, 'id')
        return res_fields

    def _parse_parameters(self, extra_params=()):
        parser = reqparse.RequestParser()
        for name, param_type in extra_params:
            parser.add_argument(name, type=param_type)
        return parser.parse_args()

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
    """ Base REST resource for SQL models. """

    # ==== GET ====

    # List related methods
    def _get_list_query(self, params, **kwargs):
        def get_order():
            order = params.get('order', 'asc')
            try:
                return self.ORDER_DICT[order]
            except KeyError:
                raise ValidationError('Invalid order. It could be asc or desc')

        # Quering
        cursor = self._build_list_query(params, **kwargs)

        # Models ordering
        sort_by_expr = params.get('sort_by', None)
        if sort_by_expr is not None:
            order = get_order()
            splitted_sort_by = re.split('\W', sort_by_expr)
            if len(splitted_sort_by) == 1:  # Simply field name
                sort_by = getattr(self.Model, splitted_sort_by[0], None)
            else:
                sort_by = sort_by_expr  # ORDER BY expression

            if sort_by is None:
                logging.warning('Ignoring sorting by %s', sort_by_expr)
            else:
                if order < 0:
                    sort_by = desc(sort_by)
                cursor = cursor.order_by(sort_by)

        return cursor

    def _prepare_model_list(self, cursor, params):
        return [self._prepare_model(model, params) for model in cursor]

    def _build_list_query(self, params, **kwargs):
        # TODO: What about joins?
        cursor = self._set_list_query_opts(self.Model.query, params)
        filter_params = self._prepare_filter_params(params)
        filter_params.update(kwargs)
        fields = self._get_show_fields(params)
        if fields:
            opts = []
            for field in self.Model.__table__.columns.keys():
                if field in fields or field in ('id',):
                    opts.append(undefer(getattr(self.Model, field)))
                else:
                    opts.append(defer(getattr(self.Model, field)))
            relation_properties = filter(
                lambda p: isinstance(p, properties.RelationshipProperty),
                self.Model.__mapper__.iterate_properties
            )
            for field in relation_properties:
                if field.key in fields:
                    cursor = cursor.options(joinedload_all(
                        getattr(self.Model, field.key)))
            if opts:
                cursor = cursor.options(*opts)

        for name, val in filter_params.iteritems():
            fltr = self._build_query_item(name, val)
            if fltr is not None:
                cursor = cursor.filter(fltr)
        return cursor

    def defer_fields(self, Model, cursor, fields):
        opts = []
        for field in Model.__table__.columns.keys():
            if field in fields or field in ('id',):
                opts.append(undefer(getattr(Model, field)))
            else:
                opts.append(defer(getattr(Model, field)))
        relation_properties = filter(
            lambda p: isinstance(p, properties.RelationshipProperty),
            Model.__mapper__.iterate_properties
        )
        for field in relation_properties:
            if field.key in fields:
                cursor = cursor.options(joinedload_all(
                    getattr(Model, field.key)))
        if opts:
            cursor = cursor.options(*opts)
        return cursor

    def _prepare_show_fields_opts(self, Model, fields):
        opts = []
        for field in Model.__table__.columns.keys():
            if field in fields or field == 'id':
                opts.append(undefer(getattr(Model, field)))
            else:
                opts.append(defer(getattr(Model, field)))
        return opts

    def _set_list_query_opts(self, cursor, params):
        return cursor

    def _paginate(self, cursor, page, per_page=20):
        paginator = cursor.paginate(page, per_page)
        return paginator.total, paginator.items

    def _build_query_item(self, name, val):
        if '.' in name:
            keys = name.split('.')
            field = getattr(self.Model, keys[0])
            return getattr(field, keys[1])(val)
        elif '->>' in name:
            field, key = name.split('->>')
            return "%s->>'%s'='%s'" % (field, key, val)
        else:
            if hasattr(self.Model, name):
                return getattr(self.Model, name) == val
            else:
                return None

    def _prepare_filter_params(self, params):
        def is_none_or_empty(val):
            return val is None or val == ''

        filter_names = [v[0] for v in self.FILTER_PARAMS]
        return dict([(k, v) for k, v in params.iteritems()
                    if not is_none_or_empty(v) and k in filter_names])

    # Details related methods
    def _get_details_query(self, params, **kwargs):
        try:
            return self._build_details_query(params, **kwargs)
        except orm_exc.NoResultFound:
            return None

    def _build_details_query(self, params, **kwargs):
        cursor = self._modify_details_query(
            self.Model.query, params).filter_by(**kwargs)

        fields = self._get_show_fields(params)
        if fields:
            opts = []
            for field in self.Model.__table__.columns.keys():
                if field in fields or field in ('id',):
                    opts.append(undefer(getattr(self.Model, field)))
                else:
                    opts.append(defer(getattr(self.Model, field)))

            relation_properties = filter(
                lambda p: isinstance(p, properties.RelationshipProperty),
                self.Model.__mapper__.iterate_properties
            )
            for field in relation_properties:
                if field.key in fields:
                    cursor = cursor.options(joinedload_all(
                        getattr(self.Model, field.key)))
            if opts:
                cursor = cursor.options(*opts)

        return cursor.one()

    def _modify_details_query(self, cursor, params):
        return cursor

    def _prepare_model(self, model, params):
        fields = self._get_show_fields(params)
        res = {}
        for field in fields:
            val = getattr(model, field, None)
            if val is None and hasattr(model, "get"):
                val = model.get(field, None)
            res[field] = val
        return res

    def _prepare_model_any(self, model, params):
        fields = self._get_all_fields()
        return dict([(field, getattr(model, field, None))
                     for field in fields])

    def _get_all_fields(self):
        return [name.replace("%s." % self.Model.__tablename__, '')
                for name in self.Model.__table__.columns.keys()]
