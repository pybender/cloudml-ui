import json

from api.base.forms import BaseForm, CharField, BooleanField, ModelField, \
    ChoiceField, ModelField, JsonField, IntegerField
from api.base.resources import ValidationError
from models import Server, Model, TestResult, \
    XmlImportHandler, ServerModelVerification


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
    params_map = JsonField()
    count = IntegerField()

    def save(self, *args, **kwargs):
        obj = super(ServerModelVerificationForm, self).save(*args, **kwargs)
        from tasks import verify_model
        verify_model.delay(
            obj.id,
            self.cleaned_data['count'])
        return obj


class VerifyForm(BaseForm):
    count = IntegerField()

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get('obj', None)
        super(VerifyForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.model.status = ServerModelVerification.STATUS_QUEUED
        self.model.save()

        from tasks import verify_model
        verify_model.delay(
            self.model.id,
            self.cleaned_data['count'])
        return self.model
