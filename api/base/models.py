from flask import has_request_context, request
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func

from api.db import JSONType
from api import app

db = app.sql_db


class BaseMixin(object):
    @declared_attr
    def __tablename__(cls):
        return _convert_name(cls.__name__)

    def _set_user(self, user):
        if user:
            field = 'updated_by' if self.id else 'created_by'
            if hasattr(self, field):
                setattr(self, field, {
                    '_id': user.id,
                    'uid': user.uid,
                    # TODO
                    # 'name': user.name
                })

    def save(self, commit=True):
        if has_request_context():
            self._set_user(getattr(request, 'user', None))
        db.session.add(self)
        if commit:
            db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class BaseModel(BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, server_default=func.now())
    updated_on = db.Column(db.DateTime, server_default=func.now(),
                           onupdate=func.current_timestamp())
    created_by = db.Column(JSONType)
    updated_by = db.Column(JSONType)


def _convert_name(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
