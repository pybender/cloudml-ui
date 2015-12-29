# Authors: Nikolay Melnik <nmelnik@upwork.com>
from cloudml import ChainedException


__all__ = ('NotFound', 'ValidationError', 'CloudmlUINotImplemented')


class CloudmlUINotImplemented(ChainedException):
    pass


class NotFound(ChainedException):
    pass


class ValidationError(ChainedException):
    """
    Base exception class for form validation, that stores
    validation errors.
    """
    def __init__(self, message, chain=None, **kwargs):
        self.errors = kwargs.pop('errors', None)
        super(ValidationError, self).__init__(message, chain)
        # replace traceback if needed
        if 'traceback' in kwargs:
            self.traceback = kwargs.pop('traceback')
