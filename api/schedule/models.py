from beatsqlalchemy.model.base import Base
from beatsqlalchemy.model.model import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule)
from api.base.models import db, BaseModel, JSONType


class PeriodicTaskScenarios(BaseModel, db.Model):
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    scenarios = db.Column(JSONType)
    interval = db.Column(JSONType)
    crontab = db.Column(JSONType)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    def __str__(self):
        return self.name
