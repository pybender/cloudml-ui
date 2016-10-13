from beatsqlalchemy.model.base import Base
from beatsqlalchemy.model.model import (PeriodicTask, CrontabSchedule, PeriodicTasks, IntervalSchedule)
"""
from api.base.models import db, BaseModel, JSONType, S3File


class Schedule(db.Model, BaseModel):
    TYPES = ['crontab', 'interval']
    __tablename__ = 'schedule'
    scenario = db.Column(JSONType)
    schedule = db.Column(db.String(30))
    type = db.Column(db.Enum(*TYPES, name='schedule_type'))
    enabled = db.Column(db.Boolean)
"""