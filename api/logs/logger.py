"""
Base classes for database logger and
init_logger method.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging


class BaseLogMessageHandler(logging.Handler):
    """
    Python logging handler, which outputs to db.

    log_type: string
        Type of the log message.
    params: dict
        Key-value dictionary of the parameters, which unique define
        the model, related to this logs.

    Table of the parameters by log type
    ===================================

    log_type                    params
    --------------------------  -----------------
    importdata_log              Dataset ID
    trainmodel_log              Model ID
    runtest_log                 Test ID
    transform_for_download_log  Dataset ID
    traintransformer_log        Transformer ID
    confusion_matrix_log        Model ID
    """

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
        from api.base.resources.exceptions import CloudmlUINotImplemented
        raise CloudmlUINotImplemented()


def init_logger(name, **kwargs):
    "Initialize the database logger"
    logger = logging.getLogger()
    logger.handlers = []
    from api import app
    if not app.config['TEST_MODE']:
        from dynamodb.logger import LogMessageHandler
        handler = LogMessageHandler(log_type=name, params=kwargs)
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
    else:
        # using standart logger for unittests
        logger.propagate = False
        logger.setLevel(logging.ERROR)
        logger.disabled = True
    return logger
