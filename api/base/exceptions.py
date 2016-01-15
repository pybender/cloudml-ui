from cloudml.exceptions import ChainedException


class BaseApiException(ChainedException):
    pass


class DBException(BaseApiException):
    pass


class InvalidOperationError(BaseApiException):
    pass
