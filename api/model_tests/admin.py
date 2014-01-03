from flask.ext.admin.model.template import macro

from api import admin
from api.base.admin import BaseAdmin
from models import TestResult, TestExample


class TestResultAdmin(BaseAdmin):
    Model = TestResult
    column_formatters = {
        'status': macro('status_with_error'),
        'model': macro('render_fk_link'),}
    column_list = ['id', 'name', 'status', 'model', 'accuracy', 'parameters',
                   'examples_count', 'examples_size', 'classes_set',
                   'memory_usage']
    column_sortable_list = (
        ('status', TestResult.status),
        ('examples_count', TestResult.examples_count),
        ('accuracy', TestResult.accuracy),
    )

admin.add_view(TestResultAdmin(
    name='Test Result', category='Tests'))


class TestExampleAdmin(BaseAdmin):
    Model = TestExample
    column_formatters = {
        'test_result': macro('render_fk_link'),
        'model': macro('render_fk_link')}
    column_list = ['id', 'name', 'example_id', 'label', 'pred_label',
                   'prob', 'model', 'test_result']
    column_sortable_list = (
        ('example_id', TestExample.example_id),
        ('label', TestExample.label),
        ('pred_label', TestExample.pred_label),
    )

admin.add_view(TestExampleAdmin(
    name='Test Example', category='Tests'))
