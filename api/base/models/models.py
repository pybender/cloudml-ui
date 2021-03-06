"""
SqlAlchemy Model Mixin classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from functools import wraps
from flask import has_request_context, request
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import Boolean

from serialization import JsonSerializableMixin
from api import app
from api.base.models.fields import JSONType
from api.base.exceptions import DBException


db = app.sql_db


class BaseMixin(JsonSerializableMixin):
    id = db.Column(db.Integer, primary_key=True)
    reason_msg = ''

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
                if column is not None:
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

    def can_edit(self):
        return True

    def can_delete(self):
        return True

    def is_authorized(self):
        return True


class BaseModel(BaseMixin):
    created_on = db.Column(db.DateTime, server_default=func.now())
    updated_on = db.Column(db.DateTime, server_default=func.now(),
                           onupdate=func.current_timestamp())
    reason_msg = 'Item is created by another user.'

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
            db.ForeignKey('user.id', ondelete='SET NULL'), index=True)

    @declared_attr
    def updated_by(cls):
        return relationship(
            "User", foreign_keys='%s.updated_by_id' % cls.__name__)

    @property
    def can_edit(self):
        if self.created_by is None:
            return True
        return self._can_modify()

    @property
    def can_delete(self):
        if self.created_by is None:
            return True
        return self._can_modify()

    @property
    def is_authorized(self):
        user = getattr(request, 'user', None)
        if user is None:
            return False
        return True

    def _can_modify(self):
        if not self.is_authorized:
            return False
        user = getattr(request, 'user', None)
        if user.email in [el[1] for el in app.config['ADMINS']]:
            return True

        return user.id == self.created_by.id


def commit_on_success(func, raise_exc=False):
    def _commit_on_success(*args, **kw):
        db = func.func_globals['db']
        try:
            return func(*args, **kw)
        except Exception, e:
            if db.session.dirty:
                db.session.rollback()
            raise DBException(e.message, e)
        else:
            if db.session.dirty:
                try:
                    db.session.commit()
                except Exception, ex:
                    db.session.rollback()
                    raise DBException(ex.message, ex)
    return wraps(func)(_commit_on_success)


class BaseDeployedEntity(object):
    """Represents entity that can be deployed to predict"""
    servers_ids = db.Column(JSONType)

    @property
    def servers(self):
        """Returns servers where model is deployed to"""
        from api.servers.models import Server
        servers = []
        if self.servers_ids is not None:
            for server_id in self.servers_ids:
                server = Server.query.get(server_id)
                if server:
                    servers.append(server)
        return sorted(servers, key=lambda x: Server.TYPES.index(x.type),
                      reverse=True)
