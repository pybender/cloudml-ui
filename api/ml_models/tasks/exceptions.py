# Authors: Nikolay Melnik <nmelnik@upwork.com>

__all__ = ['VisualizationException']


class VisualizationException(Exception):
    CLASSIFIER_NOT_SUPPORTED = 1
    ALL_WEIGHT_NOT_FILLED = 2

    def __init__(self, message, error_code=0):
        super(VisualizationException, self).__init__(message)
        self.error_code = error_code

    def __str__(self):
        return "%s (err code=%s)" % (self.message, self.error_code)
