from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func

from api import app

db = app.sql_db


class BaseModel(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def save(self):
        db.session.add(self)
        db.session.commit()


class BaseMixin(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, server_default=func.now())
    updated_on = db.Column(db.DateTime, server_default=func.now(),
                           onupdate=func.current_timestamp())
    # created_by, updated_by TODO:
