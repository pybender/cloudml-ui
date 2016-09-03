"""
This module represents resource that returns info
about application (i.e. version, description, release notes)
"""

# Authors: Anna Lysak <annalysak@cloud.upwork.com>

import os
from api import api, __version__
from api.base.resources import BaseResource, odesk_error_response, \
    ERR_INVALID_DATA


class AboutResource(BaseResource):
    """ About methods """

    def get(self, action=None):
        try:
            basedir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../'))
            with open(os.path.join(basedir, 'changelog.rst')) as fh:
                res = fh.read()
                fh.close()
            return self._render({'about': {
                'version': __version__,
                'releasenotes': res.replace('.. _changelog:', '').strip(),
            }})
        except Exception as e:
            return odesk_error_response(500, ERR_INVALID_DATA, e.message, e)


api.add_resource(AboutResource, '/cloudml/about/')
