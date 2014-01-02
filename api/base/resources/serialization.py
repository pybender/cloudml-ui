from datetime import datetime
import mongokit
from sqlalchemy import orm
from bson.objectid import ObjectId

from api.base.models import db


def encode_model(obj):
    if obj is None:
        return obj
    if isinstance(obj, mongokit.Document):
        out = encode_model(dict(obj))
    elif isinstance(obj, mongokit.cursor.Cursor):
        out = [encode_model(item) for item in obj]
    elif isinstance(obj, db.Model):
        out = {}
        for key, val in obj.__dict__.iteritems():
            if key.startswith(('__', '_sa_')):
                continue
            out[key] = encode_model(val)
    elif isinstance(obj, orm.Query):
        out = obj.all()
    elif isinstance(obj, list):
        out = [encode_model(item) for item in obj]
    elif isinstance(obj, dict):
        out = dict([(k, encode_model(v)) for (k, v) in obj.items()])
    elif isinstance(obj, datetime):
        out = str(obj)
    elif isinstance(obj, ObjectId):
        out = str(obj)
    elif isinstance(obj, int) or isinstance(obj, float):
        out = obj
    else:
        try:
            out = str(obj)
        except UnicodeEncodeError:
            out = obj.encode('utf-8')
    return out
