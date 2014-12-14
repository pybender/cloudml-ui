"""
Administrative views for models: Model, Tag, Weight, WeightsCategory
"""
from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
#from api.accounts.models import User
from models import Model, Tag, WeightsCategory, Weight, Segment, Transformer, \
    ClassifierGridParams


def classifier_type_formatter(view, context, model, name):
    classifier = model.classifier
    if classifier:
        return classifier.get('type', None)


class ModelAdmin(BaseAdmin):
    Model = Model
    column_searchable_list = ('name', )
    form_excluded_columns = ('trainer', 'weights', 'weight_categories')
    column_formatters = {
        'features_set': macro('render_fk_link'),
        'test_import_handler': macro('render_fk_link'),
        'train_import_handler': macro('render_fk_link'),
        'status': macro('status_with_error'),
        'classifier': classifier_type_formatter}
    column_list = [
        'id', 'name', 'status', 'classifier',
        'features_set', 'feature_count', 'target_variable', 'memory_usage',
        'training_time', 'test_import_handler', 'train_import_handler']
    column_sortable_list = (
        ('id', Model.id),
        ('name', Model.name),
        ('target_variable', Model.target_variable),
        ('memory_usage', Model.memory_usage),
        ('training_time', Model.training_time),
        ('status', Model.status),
        ('feature_count', Model.feature_count),
    )
    column_filters = ('status', )

admin.add_view(ModelAdmin(
    name='Model', category='Models'))


class TransformerAdmin(BaseAdmin):
    Model = Transformer
    column_list = ['id', 'type', 'name']

admin.add_view(TransformerAdmin(
    name='Transformer', category='Models'))


class TagAdmin(BaseAdmin):
    Model = Tag
    MIX_METADATA = False
    column_list = ['id', 'text', 'count']
    column_sortable_list = (
        ('text', Tag.text),
        ('count', Tag.count)
    )
    column_filters = ('count', )

admin.add_view(TagAdmin(
    name='Tag', category='Models'))


class SegmentAdmin(BaseAdmin):
    Model = Segment
    MIX_METADATA = False
    column_list = ['id', 'name', 'model']

admin.add_view(SegmentAdmin(
    name='Segment', category='Models'))


class WeightsCategoryAdmin(BaseAdmin):  # TODO: tree?
    Model = WeightsCategory
    MIX_METADATA = False
    column_formatters = {'model': macro('render_fk_link')}
    column_list = ['id', 'name', 'model', 'short_name', 'parent']
    column_sortable_list = (
        ('name', WeightsCategory.name),
        ('model', WeightsCategory.model)
    )
    #column_filters = ('model', )

admin.add_view(WeightsCategoryAdmin(
    name='Weight Category', category='Models'))


class WeightAdmin(BaseAdmin):
    Model = Weight
    MIX_METADATA = False
    column_formatters = {'model': macro('render_fk_link')}
    column_list = ['id', 'name', 'model', 'short_name',
                   'parent', 'value', 'is_positive', 'css_class']
    column_sortable_list = (
        ('name', Weight.name),
        ('model', Weight.model)
    )
    column_filters = ('name', 'is_positive', 'css_class', 'value')

admin.add_view(WeightAdmin(
    name='Weight', category='Models'))


class ClassifierGridParamsAdmin(BaseAdmin):
    Model = ClassifierGridParams
    column_formatters = {'model': macro('render_fk_link')}
    column_list = ['id', 'model', 'train_dataset', 'scoring', 'status',
                   'parameters', 'parameters_grid']

admin.add_view(ClassifierGridParamsAdmin(
    name='ClassifierGridParams', category='Models'))
