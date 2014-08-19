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

import Queue, threading, sys

def patchAsyncEmit(handler):
    base_emit = handler.emit
    queue = Queue.Queue()
    def loop():
        while True:
            record = queue.get(True) # blocks
            try :
                base_emit(record)
            except: # not much you can do when your logger is broken
                print sys.exc_info()
    thread = threading.Thread(target=loop)
    thread.daemon = True
    thread.start()
    def asyncEmit(record):
        queue.put(record)
    handler.emit = asyncEmit
    return handler


def init_logger(name, **kwargs):
    logger = logging.getLogger()
    logger.handlers = []
    from api import app
    if not app.config['TEST_MODE']:
        from dynamodb.logger import LogMessageHandler
        handler = LogMessageHandler(log_type=name, params=kwargs)
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        #patchAsyncEmit(handler)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
    else:
        logger.propagate = False
        logger.setLevel(logging.ERROR)
        logger.disabled = True
    return logger
