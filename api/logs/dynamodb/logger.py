import logging

from ..logger import BaseLogMessageHandler
from models import LogMessage

def cap(s, l):
    return s if len(s)<=l else s[0:l-3]+'...'

class LogMessageHandler(BaseLogMessageHandler):
    """ Logging handler, which outputs to amazon dynamodb. """
    def write_to_db(self, content, record):
        msg = LogMessage(
            self.log_type,
            cap(content, 64000),
            object_id=self.params['obj'],
            level=record.levelname)
        msg.save()
