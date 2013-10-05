import json

from api.resources import ValidationError


class BaseField(object):
    DEFAULT_VALUE = None

    def __init__(self, default=None):
        self.value = None
        self._default = default or self.DEFAULT_VALUE

    def clean(self, value):
        self.value = value
        return self.value


class CharField(BaseField):
    pass


class BooleanField(BaseField):
    def clean(self, value):
        value = super(BooleanField, self).clean(value)
        if value is not None:
            return value == 'true' or value == 'True'
        return None


class ChoiceField(CharField):
    def __init__(self, **kwargs):
        self._choices = kwargs.pop('choices')
        super(ChoiceField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(ChoiceField, self).clean(value)

        if value and not value in self._choices:
            raise ValidationError('please choose one of %s' % self._choices)

        return value


class DocumentField(CharField):
    def __init__(self, **kwargs):
        self.doc = kwargs.pop('doc')
        self.by_name = kwargs.pop('by_name', False)
        self.return_doc = kwargs.pop('return_doc', False)
        self.filter_params = kwargs.pop('filter_params', {})
        super(DocumentField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(DocumentField, self).clean(value)

        if value:
            if self.by_name:
                params = {'name': value}
            else:
                from bson.objectid import ObjectId
                params = {'_id': ObjectId(value)}
            params.update(self.filter_params)

            obj = self.doc.find_one(params)
            if obj is None:
                raise ValidationError('Document not found')

            if self.return_doc:
                return obj
            else:
                self.doc = obj
                return value


class JsonField(CharField):
    def clean(self, value):
        value = super(JsonField, self).clean(value)

        if value:
            try:
                return json.loads(value)
            except ValueError:
                raise ValidationError('invalid json: %s' % value)
