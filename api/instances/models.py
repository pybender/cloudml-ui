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

    def save(self, commit=True):
        BaseModel.save(self, commit=False)
        if self.is_default:
            Instance.query\
                .filter(Instance.is_default, Instance.name != self.name)\
                .update({Instance.is_default: False})
        if commit:
            db.session.commit()
