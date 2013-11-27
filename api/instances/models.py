from sqlalchemy.orm import deferred
from sqlalchemy import String, Binary, Column, Enum, Text

from api.models import BaseMixin, db


class Instance(BaseMixin, db.Model):
    """ Represents instance, which could be using for exec tasks """
    TYPES_LIST = []

    name = Column(String(200), nullable=False)
    description = deferred(Column(Text))
    ip = Column(String(200), nullable=False)
    type_ = Column(Enum(*TYPES_LIST, name='instance_types'))
    is_default = Column(Binary)
