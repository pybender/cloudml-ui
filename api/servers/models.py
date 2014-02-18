from sqlalchemy.orm import deferred

from api.base.models import BaseModel, db, JSONType


class Server(BaseModel, db.Model):
    """ Represents cloudml-predict server """
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = deferred(db.Column(db.Text))
    ip = db.Column(db.String(200), nullable=False)
    folder = db.Column(db.String(600), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    data = db.Column(JSONType)

    def save(self, commit=True):
        BaseModel.save(self, commit=False)
        if self.is_default:
            Server.query\
                .filter(Server.is_default, Server.name != self.name)\
                .update({Server.is_default: False})
        if commit:
            db.session.commit()
