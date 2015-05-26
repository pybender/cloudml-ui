"""
Custom SqlAlchemy Field classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import uuid
import os
from bson import ObjectId

from sqlalchemy.types import UserDefinedType, UnicodeText, TypeDecorator, \
    String
from sqlalchemy.dialects.postgresql.base import ischema_names
from gridfs import GridFS

from api.amazon_utils import AmazonS3Helper


__all__ = ('PostgresJSON', 'JSONType', 'GridfsFile', 'S3File')


class PostgresJSON(UserDefinedType):
    def get_col_spec(self):
        return "json"


ischema_names['json'] = PostgresJSON


# TODO: This field doesn't displays in admin part.
class JSONType(TypeDecorator):
    impl = UnicodeText

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native JSON type.
            return dialect.type_descriptor(PostgresJSON())
        else:
            return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class GridfsFile(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        from api import app

        if value is not None:
            fs = GridFS(app.db)
            value = str(fs.put(value))
        return value

    def process_result_value(self, value, dialect):
        from api import app

        if value is not None:
            fs = GridFS(app.db)
            # Returns GridOut object
            value = fs.get(ObjectId(value))
        return value


class S3File(TypeDecorator):
    impl = String

    def _get_file_path(self, value):
        from api import app
        path = app.config['DATA_FOLDER']
        return os.path.join(path, '{0!s}.dat'.format(value))

    def process_bind_param(self, value, dialect):
        if value is not None:
            helper = AmazonS3Helper()
            uid = str(uuid.uuid1().hex)
            helper.save_key_string(uid, value)
            value = uid
            filename = self._get_file_path(value)
            if os.path.exists(filename):
                os.remove(filename)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            filename = self._get_file_path(value)
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    return f.read()

            helper = AmazonS3Helper()
            value = helper.load_key(value)

            with open(filename, 'w') as f:
                f.write(str(value))
        return value
