from api.base.forms import BaseForm
from api.base.fields import CharField, BooleanField


class InstanceForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'ip', 'type')

    name = CharField()
    description = CharField()
    ip = CharField()
    type_field = CharField(name='type')  # TODO: choices
    is_default = BooleanField()
