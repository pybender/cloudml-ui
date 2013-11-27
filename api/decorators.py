from functools import wraps
from sqlalchemy.orm import exc as orm_exc

from flask import request

from api.utils import odesk_error_response
from api.accounts.models import User

# TODO: to accounts?
def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        is_authenticated = getattr(func, 'authenticated', False)

        token = request.headers.get('X-Auth-Token')

        if token:
            try:
                request.user = User.query.filter_by(
                    auth_token=User.get_hash(token)).one()
                is_authenticated = True
            except orm_exc.NoResultFound:
                request.user = None

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
