# Authors: Nikolay Melnik <nmelnik@upwork.com>

__all__ = ('NotFound', 'ValidationError')


class NotFound(Exception):
    pass


class ValidationError(Exception):
    """
    Base exception class for form validation, that stores
    validation errors.
    """
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors', None)
        self.traceback = kwargs.pop('traceback', None)
        super(ValidationError, self).__init__(*args, **kwargs)
