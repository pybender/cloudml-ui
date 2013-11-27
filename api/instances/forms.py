from api.base.forms import BaseForm, BaseForm
from api.resources import ValidationError
from models import Instance


class InstanceAddForm(BaseForm):
    fields = ('name', 'description', 'ip', 'type', 'is_default', )

    def clean_is_default(self, value):
        return value == 'true'

    def clean_name(self, value):
        if not value:
            raise ValidationError('name is required')
        return value

    def clean_type(self, value):
        # if not type in ImportHandler.TYPE_CHOICES:
        #     raise ValidationError('invalid')
        return value

    def clean_ip(self, value):
        if not value:
            raise ValidationError('data is required')
        return value

    def save(self):
        instance = BaseForm.save(self)
        if instance.is_default:
            instances = Instance.collection
            instances.update({'_id': {'$ne': instance._id}},
                             {"$set": {"is_default": False}},
                             multi=True)
        return instance


class InstanceEditForm(BaseForm):
    fields = ('name', 'is_default', )

    def clean_is_default(self, value):
        return value == 'true'

    def _field_changed(self, name):
        return getattr(self.obj, name) != self.cleaned_data[name]

    def save(self):
        default_changed = self._field_changed('is_default')
        instance = BaseForm.save(self)
        if default_changed:
            instances = Instance.collection
            instances.update({'_id': {'$ne': instance._id}},
                             {"$set": {"is_default": False}},
                             multi=True)
        return instance
