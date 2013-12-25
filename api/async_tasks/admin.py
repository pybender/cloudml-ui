from api import admin
from api.base.admin import BaseAdmin
from models import AsyncTask


class AsyncTaskAdmin(BaseAdmin):
    Model = AsyncTask

admin.add_view(AsyncTaskAdmin())
