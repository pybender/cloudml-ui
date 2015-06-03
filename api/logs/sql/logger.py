# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.logs.logger import BaseLogMessageHandler


class LogMessageHandler(BaseLogMessageHandler):
    def write_to_db(self, content, record):
        from models import LogMessage
        msg = LogMessage()
        msg.content = content[:600]
        msg.type = self.log_type
        msg.params = self.params
        msg.level = record.levelname
        msg.save()
