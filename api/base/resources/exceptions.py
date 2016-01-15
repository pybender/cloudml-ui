# Authors: Nikolay Melnik <nmelnik@upwork.com>
from api.base.exceptions import BaseApiException


__all__ = ('NotFound', 'ValidationError', 'NotImplemented')


class NotImplemented(BaseApiException):
    pass


class NotFound(BaseApiException):
    pass


class ValidationError(BaseApiException):
    """
    Base exception class for form validation, that stores
    validation errors and traceback for each error.
    """
    def __init__(self, message, chain=None, **kwargs):
        self.errors = kwargs.pop('errors', None)
        super(ValidationError, self).__init__(message, chain)
