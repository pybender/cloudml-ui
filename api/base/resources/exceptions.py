class NotFound(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors', None)
        super(ValidationError, self).__init__(*args, **kwargs)
