# Models, Tags and Weights goes here
from api.base.models import BaseModel, db


class Model(BaseModel, db.Model):
    name = db.Column(db.String(200), nullable=False)
