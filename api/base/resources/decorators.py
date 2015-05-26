"""
Various resource's method decorators
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from functools import wraps
from sqlalchemy.orm import exc as orm_exc

from flask import request

from .utils import odesk_error_response
from api.accounts.models import User


__all__ = ('authenticate', 'public', 'public_actions')


def authenticate(func):
    """
    Decorator for views that checks that the user is logged in, raising HTTP401
    error.
    """
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
    """
    Marks some resource's methods as public.
    """
    func.authenticated = True
    return func


def public_actions(actions=None):
    """
    Marks some resource's actions as public
    (no need user authentication to acess to them)
    """
    def _public_actions(func):
        func.authenticated = False
        func.public_actions = actions
        return func
    return _public_actions
