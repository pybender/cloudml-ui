from functools import wraps
from flask import has_request_context, request
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import Boolean

from serialization import JsonSerializableMixin
from api import app

db = app.sql_db


class BaseMixin(JsonSerializableMixin):
    id = db.Column(db.Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        from ..utils import convert_name
        return convert_name(cls.__name__)

    def _set_user(self, user=None):
        if has_request_context():
            user = getattr(request, 'user', None)
        if user:
            self.updated_by = user
            if self.id is None:
                self.created_by = user

    def to_dict(self):
        kwargs = {}
        for f in self.FIELDS_TO_SERIALIZE:
            val = getattr(self, f)
            if val is not None:
                column = self.__table__.columns.get(f, None)
                if not column is None:
                    if isinstance(column.type, Boolean):
                        val = str(val).lower()
                kwargs[f] = val
        return kwargs

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


def commit_on_success(func, raise_exc=False):
    def _commit_on_success(*args, **kw):
        db = func.func_globals['db']
        try:
            return func(*args, **kw)
        except:
            if db.session.dirty:
                db.session.rollback()
            raise
        else:
            if db.session.dirty:
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                    raise
    return wraps(func)(_commit_on_success)
