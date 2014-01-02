from sqlalchemy.orm import deferred

from api.base.models import BaseModel, db


class Instance(BaseModel, db.Model):
    """ Represents instance, which could be using for exec tasks """
    TYPES_LIST = ['small', 'large']

    name = db.Column(db.String(200), nullable=False, unique=True)
    description = deferred(db.Column(db.Text))
    ip = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES_LIST, name='instance_types'),
                     nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    def save(self):
        BaseModel.save(self)
        if self.is_default:
            Instance.query\
                .filter(Instance.is_default, Instance.id != self.id)\
                .update({Instance.is_default: False})
            db.session.commit()
