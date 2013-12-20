from .models import BaseMixin, BaseModel, db
from .fields import JSONType, GridfsFile
from .serialization import JsonSerializableMixin


def assertion_msg(field, err):
    return [{'name': field, 'error': err}]
