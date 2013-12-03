from api.base.forms import BaseForm
from api.base.fields import CharField, BooleanField
from api.resources import ValidationError
from models import Instance


class InstanceForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'ip', 'type')

    name = CharField()
    description = CharField()
    ip = CharField()
    type_field = CharField(name='type')  # TODO: ChoiceField
    is_default = BooleanField()

    def clean_name(self, value, field):
        query = Instance.query.filter_by(name=value)
        if self.obj.id:
            query = query.filter(Instance.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError('name should be unique')
        return value
