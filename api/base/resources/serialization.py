from datetime import datetime, date, time
import mongokit
from sqlalchemy import orm
from bson.objectid import ObjectId

from api import app
from api.base.models.serialization import JsonSerializableMixin


def encode_model(obj):
    if obj is None:
        return obj

    if isinstance(obj, mongokit.Document):
        out = encode_model(dict(obj))
    elif isinstance(obj, mongokit.cursor.Cursor):
        out = [encode_model(item) for item in obj]
    elif isinstance(obj, JsonSerializableMixin):
        out = obj.__json__()
    elif isinstance(obj, app.sql_db.Model):
        data = obj.__dict__
        # TODO: Check whether it could cause any issues?
        if '_sa_instance_state' in data:
            del data['_sa_instance_state']
        out = encode_model(data)
    elif isinstance(obj, orm.Query):
        out = list(obj.all())
    elif isinstance(obj, list):
        out = [encode_model(item) for item in obj]
    elif isinstance(obj, dict):
        out = dict([(k, encode_model(v)) for (k, v) in obj.items()])
    elif isinstance(obj, datetime):
        out = str(obj)
    elif isinstance(obj, ObjectId):
        out = str(obj)
    else:
        try:
            out = str(obj)
        except UnicodeEncodeError:
            out = obj.encode('utf-8')
    return out
