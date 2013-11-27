from sqlalchemy.orm import deferred
from sqlalchemy import String, Binary, Column, Enum, Text

from api.base.models import BaseModel, db


class Instance(BaseModel, db.Model):
    """ Represents instance, which could be using for exec tasks """
    TYPES_LIST = ['small', 'large']

    name = Column(String(200), nullable=False)
    description = deferred(Column(Text))
    ip = Column(String(200), nullable=False)
    type = Column(Enum(*TYPES_LIST, name='instance_types'))
    is_default = Column(Binary, default=False)
