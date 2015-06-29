"""
Datasource that used to db exports model declared here.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from sqlalchemy.orm import deferred, validates
from api.base.models import db, BaseModel, JSONType, assertion_msg


class PredefinedDataSource(db.Model, BaseModel):
    """
    Datasource that used to db exports
    """
    TYPE_REQUEST = 'http'
    TYPE_SQL = 'sql'
    TYPES_LIST = (TYPE_REQUEST, TYPE_SQL)

    VENDOR_POSTGRES = 'postgres'
    VENDORS_LIST = (VENDOR_POSTGRES, )

    name = db.Column(db.String(200), nullable=False, unique=True)
    type = db.Column(db.Enum(*TYPES_LIST, name='datasource_types'),
                     default=TYPE_SQL)
    # sample: {"conn": basestring, "vendor": basestring}
    db = deferred(db.Column(JSONType))

    @validates('db')
    def validate_db(self, key, db):
        self.validate_db_fields(db)
        return db

    @classmethod
    def validate_db_fields(cls, db):
        key = 'db'
        assert 'vendor' in db, assertion_msg(key, 'vendor is required')
        assert db['vendor'] in cls.VENDORS_LIST, assertion_msg(
            key, 'choose vendor from %s' % ', '.join(cls.VENDORS_LIST))
        assert 'conn' in db, assertion_msg(key, 'conn is required')
