import json

from sqlalchemy.types import UserDefinedType, UnicodeText, TypeDecorator
from sqlalchemy.dialects.postgresql.base import ischema_names


class PostgresJSON(UserDefinedType):
    def get_col_spec(self):
        return "json"


ischema_names['json'] = PostgresJSON


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
