from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from models import FeatureSet, Feature, NamedFeatureType, \
    PredefinedClassifier, PredefinedTransformer, PredefinedScaler


class FeatureSetAdmin(BaseAdmin):
    Model = FeatureSet
    column_list = ['id', 'schema_name', 'features_count', 'target_variable']
    column_sortable_list = (
        ('name', FeatureSet.schema_name)
    )
    column_sortable_list = (
        ('id', FeatureSet.id),
        ('schema_name', FeatureSet.schema_name),
        ('features_count', FeatureSet.features_count)
    )
    column_filters = ('features_count', 'target_variable')

admin.add_view(FeatureSetAdmin(
    name='Feature Set', category='Features'))


class FeatureAdmin(BaseAdmin):
    Model = Feature
    column_formatters = {
        'feature_set': macro('render_fk_link'),
        'created_by': macro('render_fk_link'),
        'updated_by': macro('render_fk_link'),
    }

admin.add_view(FeatureAdmin(
    name='Feature', category='Features'))


class NamedFeatureTypeAdmin(BaseAdmin):
    Model = NamedFeatureType
    column_exclude_list = ('params', )
    column_formatters = {
        'created_by': macro('render_fk_link'),
        'updated_by': macro('render_fk_link'),
    }

admin.add_view(NamedFeatureTypeAdmin(
    name='Named Feature Type', category='Predefined'))


class PredefinedClassifierAdmin(BaseAdmin):
    Model = PredefinedClassifier
    column_exclude_list = ('params', )
    column_formatters = {
        'created_by': macro('render_fk_link'),
        'updated_by': macro('render_fk_link'),
    }

admin.add_view(PredefinedClassifierAdmin(
    name='Classifier', category='Predefined'))


class PredefinedScalerAdmin(BaseAdmin):
    Model = PredefinedScaler
    column_exclude_list = ('params', )
    column_formatters = {
        'created_by': macro('render_fk_link'),
        'updated_by': macro('render_fk_link'),
    }

admin.add_view(PredefinedScalerAdmin(
    name='Scaler', category='Predefined'))


class PredefinedTransformerAdmin(BaseAdmin):
    Model = PredefinedTransformer
    #column_exclude_list = ('params', )
    column_formatters = {
        'created_by': macro('render_fk_link'),
        'updated_by': macro('render_fk_link'),
    }

admin.add_view(PredefinedTransformerAdmin(
    name='Transformer', category='Predefined'))
