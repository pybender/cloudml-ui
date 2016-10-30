# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import celery
import functools
import collections
from base64 import b64encode, b64decode
import pickle

from api import app
from api.base.exceptions import ApiBaseException



db_session = app.sql_db.session


def get_task_traceback(exc):
    e = TaskException(exc.message, exc)
    if e.traceback:
        return json.dumps(e.traceback)
    return ''


class TaskException(ApiBaseException):
      pass


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

class UnwrapArgs(object):
    def _jsonSupport( *args ):
        def default( self, xObject ):
            return { 'type': 'UnwrapArgs', 'args': xObject() }

        def objectHook( obj ):
            if 'type' not in obj:
                return obj
            if obj[ 'type' ] != 'UnwrapArgs':
                return obj
            return UnwrapArgs( obj[ 'args' ] )
        json.JSONEncoder.default = default
        json._default_decoder = json.JSONDecoder( object_hook = objectHook )

    _jsonSupport()

    def __init__(self, contents):
        self.contents = contents

    def __call__(self):
        return self.contents

    def to_json(self):  # New special method.
        print ("UnwrapArgs to_json")
        return "{'name': 'NM'}"

    def default(self, obj):
        print ("UnwrapArgs default")
#        if isinstance(obj, (list, dict, str, int, float, bool, type(None))):
#            return super(UnwrapArgs, self).default(obj)
#        return {'_python_object': b64encode(pickle.dumps(obj)).decode('utf-8')}

        if isinstance(obj, collections.Set):
            return dict(_set_object=list(obj))
        else:
            return json.JSONEncoder.default(self, obj)

def wrapchain(f):
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        print ("_wrapper:", args, kwargs)
        print ("_wrapper 01:", args[0], type(args[0]))
        if type(args[0]) == UnwrapArgs:
            print ("_wrapper 02:", list(args[0]()))
            inargs = list(args[0]())
            lastargs = args[1:]
            args = []
            for a in inargs:
                if isinstance(a, dict):
                    kwargs.update(a)
                elif isinstance(a, (list, tuple)):
                    args.extend(a)
                else:
                    args.append(a)
            args = list(args) + list(lastargs)
        result = f(*args, **kwargs)
        if type(result) == tuple and celery.current_task.request.callbacks:
            return UnwrapArgs(result)
        else:
            return result
    return _wrapper