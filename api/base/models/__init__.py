from .models import BaseMixin, BaseModel, db, commit_on_success
from .fields import JSONType, GridfsFile, S3File
from .serialization import JsonSerializableMixin


def assertion_msg(field, err):
    return [{'name': field, 'error': err}]
