"""
Instance related forms.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.base.forms import BaseForm, CharField, BooleanField, \
    UniqueNameField, ChoiceField
from api.base.resources import ValidationError
from models import Instance


class InstanceForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'ip', 'type')

    name = UniqueNameField(Model=Instance)
    description = CharField()
    ip = CharField()
    type_field = ChoiceField(
        choices=Instance.TYPES_LIST, name='type')
    is_default = BooleanField()
