from flask import has_request_context, request
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from sqlalchemy.orm import relationship

from serialization import JsonSerializableMixin
from api import app

db = app.sql_db


class BaseMixin(JsonSerializableMixin):
    id = db.Column(db.Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        from ..utils import convert_name
        return convert_name(cls.__name__)

    def _set_user(self, user):
        if user:
            field = 'updated_by' if self.id else 'created_by'
            if hasattr(self, field):
                setattr(self, field, user)

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
    created_on = db.Column(db.DateTime, server_default=func.now())
    updated_on = db.Column(db.DateTime, server_default=func.now(),
                           onupdate=func.current_timestamp())

    @declared_attr
    def created_by_id(cls):
        return db.Column(
            db.ForeignKey('user.id', ondelete='SET NULL'))

    @declared_attr
    def created_by(cls):
        return relationship(
            "User", foreign_keys='%s.created_by_id' % cls.__name__)

    @declared_attr
    def updated_by_id(cls):
        return db.Column(
            db.ForeignKey('user.id', ondelete='SET NULL'))

    @declared_attr
    def updated_by(cls):
        return relationship(
            "User", foreign_keys='%s.updated_by_id' % cls.__name__)
