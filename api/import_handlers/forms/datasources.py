# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.base.forms import BaseForm, CharField, JsonField, \
    ChoiceField, ValidationError
from api.import_handlers.models import PredefinedDataSource


class PredefinedDataSourceForm(BaseForm):
    """
    DataSource add/edit form
    """
    NO_REQUIRED_FOR_EDIT = True
    required_fields = ('name', 'type')

    name = CharField()
    type_field = ChoiceField(
        choices=PredefinedDataSource.TYPES_LIST, name='type')
    db = JsonField()

    def clean_name(self, value, field):
        query = PredefinedDataSource.query.filter_by(name=value)
        if self.obj.id:
            query = query.filter(PredefinedDataSource.id != self.obj.id)
        count = query.count()
        if count:
            raise ValidationError(
                "DataSource with name \"%s\" already exist. "
                "Please choose another one." % value)
        return value
