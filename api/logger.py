import logging
from mongotools.pubsub import Channel

from api import app


class MongoHandler(logging.Handler):
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


def init_logger(name, **kwargs):
    logger = logging.getLogger()
    handler = MongoHandler(name=name, params=kwargs)
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = True
    return logger
