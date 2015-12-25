# Authors: Nikolay Melnik <nmelnik@upwork.com>

from datetime import timedelta
from functools import update_wrapper, wraps
import json
import pickle
import logging
import re
import translitcodec
import sys
try:
    from pymongo.bson import BSON
except ImportError:
    from bson import BSON
    from time import time


from flask import make_response, request, current_app, jsonify
from api import app
from cloudml import traceback_info, ChainedException


ERR_INVALID_CONTENT_TYPE = 1000
ERR_NO_SUCH_MODEL = 1001
ERR_NO_MODELS = 1002
ERR_STORING_MODEL = 1003
ERR_LOADING_MODEL = 1004
ERR_INVALID_DATA = 1005
ERR_INVALID_METHOD = 1006
ERR_PICKLING_MODEL = 1007
ERR_UNPICKLING_MODEL = 1008
ERR_NO_SUCH_IMPORT_HANDLER = 1009


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def _add_cors_headers(
        h, origin='*',
        methods=', '.join(('GET', 'OPTIONS', 'DELETE', 'PUT', 'POST')),
        allow_headers='accept, origin, content-type, X-Auth-Token',
        max_age=21600):

    h['Access-Control-Allow-Origin'] = origin
    h['Access-Control-Allow-Methods'] = methods
    h['Access-Control-Max-Age'] = max_age
    if allow_headers is not None:
        h['Access-Control-Allow-Headers'] = allow_headers


def odesk_error_response(status, code, message, exception=None,
                         traceback=None, errors=None):
    """
    Creates a JSON error response that is compliant with
    https://sites.google.com/a/odesk.com/eng/Home/FunctionalSpecifications/webservices-error-handling-enhancements-frd

    Keyword arguments
    status -- The HTTP status code to return.
    code -- Internal application's error code.
    message -- A text describing the application's error.
    debug -- Additional debug information, to be added only if server is
             running on debug mode.
    """

    if traceback is None and status == 400 or status >= 500:
        if exception is not None and isinstance(exception, ChainedException):
            traceback = exception.traceback
        else:
            traceback = traceback_info()

    result = {'response': {
              'server_time': time(),
              'error': {'status': status, 'code': code,
                        'message': message,
                        'traceback': traceback,
                        'errors': errors}}}
    if app.debug:
        result['response']['error']['debug'] = app.debug

    response = jsonify(result)
    h = response.headers
    response.status_code = status

    h['Content-type'] = 'application/json'
    h['X-Odesk-Error-Code'] = code
    h['X-Odesk-Error-Message'] = ''.join(message.splitlines())

    # CORS headers
    _add_cors_headers(h)

    return response


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            _add_cors_headers(h, origin=origin, methods=get_methods(),
                              max_age=max_age, allow_headers=headers)
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def get_doc_size(doc):
    """
    Get document size in bytes

    :Parameters:
        - `doc`: string or dict

    """
    if not isinstance(doc, dict):
        doc = json.loads(doc)

    return len(BSON.encode(doc))


def _select(Cls, field_names, filter_params, extra_fields={}):
    field_names = ['short_name', 'name', 'css_class',
                   'value', 'segment_id', 'value2']
    fields = [getattr(Cls, name) for name in field_names]
    for name, field in extra_fields.iteritems():
        fields.append(field)
        field_names.append(name)
    objects = app.sql_db.session.query(*fields).filter_by(**filter_params)
    return [dict(zip(field_names, obj)) for obj in objects]
