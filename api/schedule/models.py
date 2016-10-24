from beatsqlalchemy.model.base import Base
from beatsqlalchemy.model.model import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule)
from api.base.models import db, BaseModel, JSONType


class PeriodicTaskScenarios(BaseModel, db.Model):
    name = db.Column(db.String(100), nullable=False)
    descriptions = db.Column(db.String(500))
    scenarios = db.Column(JSONType)
    interval = db.Column(JSONType)
    crontab = db.Column(JSONType)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    TYPE_INTERVAL = 'interval'
    TYPE_CRONTAB = 'crontab'

    @property
    def type(self):
        if self.interval != {}:
            return self.TYPE_INTERVAL
        else:
            return self.TYPE_CRONTAB


    def __str__(self):
        return self.name
