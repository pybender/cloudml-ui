from api.base.forms import BaseForm, CharField, BooleanField, ModelField, \
    ChoiceField, ModelField
from api.base.resources import ValidationError
from models import Server, Model, TestResult, \
    XmlImportHandler


class ServerForm(BaseForm):
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'ip', 'folder', 'type')

    name = CharField()
    description = CharField()
    ip = CharField()
    folder = CharField()
    is_default = BooleanField()
    type = ChoiceField(choices=Server.TYPES)

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


class ServerModelVerificationForm(BaseForm):
    required_fields = ('server_id', 'model_id', 'test_result_id')

    server_id = ModelField(model=Server)
    model_id = ModelField(model=Model)
    import_handler_id = ModelField(model=XmlImportHandler)
    test_result_id = ModelField(model=TestResult)
    description = CharField()

    # def save(self, *args, **kwargs):
    #     obj = super(ServerModelVerificationForm, self).save(commit=False, *args, **kwargs)
    #     import pdb
    #     pdb.set_trace()
    #     obj.import_handler = obj.description['import_handler']
    #     obj.save()
