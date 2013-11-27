import logging
from mongotools.pubsub import Channel

from api import app


class MongoHandler(logging.Handler):  # pragma: no cover
    """
    Logging handler, which supports pub/sub
    """
    def __init__(self, name='noname', params={}):
        super(MongoHandler, self).__init__()
        self.params = params
        self.name = name

    def emit(self, record):
        chan = Channel(app.db, 'log')
        chan.ensure_channel()
        try:
            msg = self.format(record)
            context = {'msg': msg}
            context.update(self.params)
            chan.pub(self.name, context)
        except:
            self.handleError(record)


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


class MongoLogMessageHandler(BaseLogMessageHandler):
    """ Logging handler, which outputs to mongodb LogMessage model. """
    def write_to_db(self, content, record):
        msg = app.db.LogMessage()
        msg['content'] = content
        msg['type'] = self.log_type
        msg['params'] = self.params
        msg['level'] = record.levelname
        msg.save(validate=True)


class LogMessageHandler(BaseLogMessageHandler):
    def write_to_db(self, content, record):
        from api.logs.models import LogMessage
        msg = LogMessage()
        msg.content = content
        msg.type = self.log_type
        msg.params = self.params
        msg.level = record.levelname
        msg.save()


def init_logger(name, **kwargs):
    logger = logging.getLogger()
    #handler = MongoHandler(name=name, params=kwargs)
    handler = LogMessageHandler(log_type=name, params=kwargs)
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    return logger
