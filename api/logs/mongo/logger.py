import logging

from ..logger import BaseLogMessageHandler
from api import app


class MongoHandler(logging.Handler):  # pragma: no cover
    """ Logging handler, which supports pub/sub """
    def __init__(self, name='noname', params={}):
        super(MongoHandler, self).__init__()
        self.params = params
        self.name = name

    def emit(self, record):
        from mongotools.pubsub import Channel
        chan = Channel(app.db, 'log')
        chan.ensure_channel()
        try:
            msg = self.format(record)
            context = {'msg': msg}
            context.update(self.params)
            chan.pub(self.name, context)
        except:
            self.handleError(record)


class LogMessageHandler(BaseLogMessageHandler):
    """ Logging handler, which outputs to mongodb LogMessage model. """
    def write_to_db(self, content, record):
        msg = app.db.LogMessage()
        msg['content'] = content
        msg['type'] = self.log_type
        msg['params'] = self.params
        msg['level'] = record.levelname
        msg.save(validate=True)
