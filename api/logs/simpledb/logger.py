import logging

from ..logger import BaseLogMessageHandler
from models import LogMessage


class LogMessageHandler(BaseLogMessageHandler):
    """ Logging handler, which outputs to amazon simledb. """
    def write_to_db(self, content, record):
        msg = LogMessage(
            self.log_type,
            content,
            object_id=self.params['obj'],
            record.levelname)
        msg.save()
