# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api import admin
from api.base.admin import BaseAdmin
from models import AsyncTask


class AsyncTaskAdmin(BaseAdmin):
    Model = AsyncTask
    column_searchable_list = ('task_name', )
    column_filters = ['task_name']
    column_list = ['id', 'task_name', 'object_id', 'object_type',
                   'result', 'error']

admin.add_view(AsyncTaskAdmin())
