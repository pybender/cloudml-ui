from functools import wraps

from flask import request

from api import app
from api.utils import odesk_error_response


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
