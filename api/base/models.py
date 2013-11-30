from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from api.db import JSONType

from api import app

db = app.sql_db


class BaseMixin(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def save(self, commit=True):
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
    # created_by, updated_by TODO:


class BasePredefinedItemModel(BaseModel):
    name = db.Column(db.String(200), nullable=False)
    params = db.Column(JSONType)

    # @declared_attr
    # def __repr__(self):
    #     return '<%s %s>' % (self.__name__.lower(), self.type)
