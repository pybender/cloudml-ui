from api.base.forms import BaseForm, CharField, BooleanField, ModelField
from api.base.resources import ValidationError
from models import Server


class ServerForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'ip', 'folder')

    name = CharField()
    description = CharField()
    ip = CharField()
    folder = CharField()
    is_default = BooleanField()

    def clean_name(self, value, field):
        query = Server.query.filter_by(name=value)
        if self.obj.id:
            query = query.filter(Server.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError('name should be unique')
        return value


class ChooseServerForm(BaseForm):
    server = ModelField(model=Server, return_model=True)
