from cloudml import ChainedException


class ApiBaseException(ChainedException):
    pass


class InvalidOperationError(ApiBaseException):
    pass


class DBException(ApiBaseException):
    pass