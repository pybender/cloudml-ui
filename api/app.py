"""
This module main application class and gather all imports together.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import re
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.routing import BaseConverter

__all__ = ["create_app"]


class App(Flask):

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        self.config.from_object('api.config')
        self.url_map.converters['regex'] = RegExConverter
        self.init_sql_db()

    @property
    def db(self):
        if not hasattr(self, '_db'):
            self.init_db()
        return self._db

    def init_db(self):
        db_name = self.config['DATABASE_NAME']

    @property
    def sql_db(self):
        return self._sql_db

    def init_sql_db(self):
        self._sql_db = SQLAlchemy(self)


def create_app():
    return App(__name__)


class RegExConverter(BaseConverter):
    """
    Converter that allows routing to specific functions according
    to given regular expression.
    """
    def __init__(self, url_map, *items):
        super(RegExConverter, self).__init__(url_map)
        self.regex = items[0]
