import logging


class BaseLogMessageHandler(logging.Handler):
    """ Logging handler, which outputs to db. """

    def __init__(self, log_type='noname', params={}):
        super(BaseLogMessageHandler, self).__init__()
        self.params = params
        self.log_type = log_type

    def emit(self, record):
        content = self.format(record)
        if 'DeprecationWarning' in content:
            return

        self.write_to_db(content, record)

    def write_to_db(self, content, record):
        raise NotImplemented()


def init_logger(name, **kwargs):
    from dynamodb.logger import LogMessageHandler
    logger = logging.getLogger()
    handler = LogMessageHandler(log_type=name, params=kwargs)
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers = []
    #logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    return logger
