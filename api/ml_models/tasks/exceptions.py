# Authors: Nikolay Melnik <nmelnik@upwork.com>
from api.base.tasks import TaskException


__all__ = ['VisualizationException']


class VisualizationException(TaskException):
    CLASSIFIER_NOT_SUPPORTED = 1
    ALL_WEIGHT_NOT_FILLED = 2

    def __init__(self, message, chain=None, error_code=0):
        super(VisualizationException, self).__init__(message, chain)
        self.error_code = error_code

    def __str__(self):
        return "%s (err code=%s)" % (self.message, self.error_code)
