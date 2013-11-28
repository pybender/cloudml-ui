from api.base.forms import BaseForm
from api.base.fields import CharField, ChoiceField, BooleanField
from api.models import Instance, ImportHandler


class InstanceAddForm(BaseForm):
    name = CharField()
    description = CharField()
    ip = CharField()
    type = ChoiceField(choices=ImportHandler.TYPES)
    is_default = BooleanField()

    def save(self):
        instance = super(InstanceAddForm, self).save(self)
        # TODO
        # if instance.is_default:
        #     instances = Instance.collection
        #     instances.update({'_id': {'$ne': instance._id}},
        #                      {"$set": {"is_default": False}},
        #                      multi=True)
        return instance


class InstanceEditForm(BaseForm):
    name = CharField()
    is_default = BooleanField()

    def _field_changed(self, name):
        return getattr(self.obj, name) != self.cleaned_data[name]

    def save(self):
        default_changed = self._field_changed('is_default')
        instance = BaseForm.save(self)
        # TODO
        # if default_changed:
        #     instances = Instance.collection
        #     instances.update({'_id': {'$ne': instance._id}},
        #                      {"$set": {"is_default": False}},
        #                      multi=True)
        return instance
