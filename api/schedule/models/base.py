#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base


class TimestampModel(object):
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, onupdate=datetime.utcnow)
    utc_fresh_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, doc="utc")

    @classmethod
    def filter_by(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs)

    @classmethod
    def get_or_create(cls, session_obj, defaults=None, **kwargs):
        obj = session_obj.query(cls).filter_by(**kwargs).first()
        if obj:
            return obj, False
        else:
            params = dict((k, v) for k, v in kwargs.iteritems())
            params.update(defaults or {})
            obj = cls(**params)
            return obj, True

    @classmethod
    def update_or_create(cls, session_obj, defaults=None, **kwargs):
        obj = session_obj.query(cls).filter_by(**kwargs).first()
        if obj:
            for key, value in defaults.iteritems():
                setattr(obj, key, value)
            created = False
        else:
            params = dict((k, v) for k, v in kwargs.iteritems())
            params.update(defaults or {})
            obj = cls(**params)
            created = True
        return obj, created

Base = declarative_base(cls=TimestampModel)
