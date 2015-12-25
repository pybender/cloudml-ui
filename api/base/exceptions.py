from cloudml import ChainedException


class CloudmlUIException(ChainedException):
    pass


class CloudmlDBException(ChainedException):
    pass


class CloudmlUIValueError(ChainedException):
    pass


class InvalidOperationError(ChainedException):
    pass
