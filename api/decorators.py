import json
import logging
from functools import wraps

from flask import request
from flask.exceptions import JSONBadRequest
from flask.ext.restful import reqparse, abort
# from sqlalchemy.orm.exc import NoResultFound

from api import app
from api.utils import ERR_NO_SUCH_MODEL, odesk_error_response, \
    ERR_INVALID_DATA
from api.serialization import BriefDetailsEncoder, FullDetailsEncoder
from core.trainer.trainer import ItemParseException


def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        is_authenticated = getattr(func, 'authenticated', False)

        token = request.headers.get('X-Auth-Token')

        if token:
            user = app.db.User.find_one({
                'auth_token': app.db.User.get_hash(token)
            })
            if user:
                is_authenticated = True
                request.user = user

        _public_actions = getattr(func, 'public_actions', False)
        if _public_actions:
            action = kwargs.get('action')
            if action and action in _public_actions:
                is_authenticated = True

        if is_authenticated:
            return func(*args, **kwargs)

        return odesk_error_response(401, 401, 'Unauthorized')
    return wrapper


def public(func):
    func.authenticated = True
    return func


def public_actions(actions=None):
    def _public_actions(func):
        func.authenticated = False
        func.public_actions = actions
        return func
    return _public_actions


def render(brief=True, code=200):
    def wrap(func, *args, **kwargs):
        def wrapper(self, *args, **kwargs):
            try:
                context = func(self, *args, **kwargs)
                encoder = BriefDetailsEncoder if brief else FullDetailsEncoder
                resp = json.dumps(context, cls=encoder,
                                  indent=None if request.is_xhr else 2)
                return app.response_class(resp,
                                          mimetype='application/json'), code
            # except NoResultFound, exc:
            #     return odesk_error_response(404, ERR_NO_SUCH_MODEL,
            #                                 exc.message or 'Object doesn\'t exist')
            except ItemParseException, exc:
                logging.error("Exception: %s", exc)
                return odesk_error_response(400, ERR_INVALID_DATA,
                                            exc.message)
            except JSONBadRequest, exc:
                logging.error("Exception: %s", exc)
                return odesk_error_response(400, ERR_INVALID_DATA,
                                            exc.message)
            except Exception, exc:
                logging.error("Exception: %s", exc)
                return odesk_error_response(500, ERR_INVALID_DATA,
                                            exc.message)
        return wrapper
    return wrap
