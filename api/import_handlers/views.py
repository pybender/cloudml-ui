import json
from flask import Response
from sqlalchemy.orm import undefer

from api import api
from api.resources import BaseResourceSQL, NotFound, ValidationError
from api.decorators import public_actions
from models import ImportHandler, DataSet
from forms import ImportHandlerAddForm, ImportHandlerEditForm, \
    DataSetAddForm, DataSetEditForm


class ImportHandlerResource(BaseResourceSQL):
    """
    Import handler API methods
    """
    Model = ImportHandler

    OBJECT_NAME = 'import_handler'
    post_form = ImportHandlerAddForm
    put_form = ImportHandlerEditForm
    GET_ACTIONS = ('download', )

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(ImportHandlerResource, self).get(*args, **kwargs)

    def _modify_details_query(self, cursor):
        return cursor.options(undefer('data'))

    def _get_download_action(self, **kwargs):
        """
        Downloads importhandler data file.
        """
        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        content = json.dumps(model.data)
        resp = Response(content)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = 'attachment; \
filename=importhandler-%s.json' % model.name
        return resp

api.add_resource(ImportHandlerResource, '/cloudml/importhandlers/')


class DataSetResource(BaseResourceSQL):
    """
    DataSet API methods
    """
    Model = DataSet

    OBJECT_NAME = 'dataset'
    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('generate_url', )
    PUT_ACTIONS = ('reupload', 'reimport')
    post_form = DataSetAddForm
    put_form = DataSetEditForm

    def _get_generate_url_action(self, **kwargs):
        ds = self._get_details_query(None, None, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        url = ds.get_s3_download_url()
        return self._render({self.OBJECT_NAME: ds.id,
                             'url': url})

    def _put_reupload_action(self, **kwargs):
        from api.tasks import upload_dataset
        dataset = self._get_details_query(None, None, **kwargs)
        if dataset.status == dataset.STATUS_ERROR:
            dataset.status = dataset.STATUS_IMPORTING
            dataset.save()
            upload_dataset.delay(dataset.id)
        return self._render(self._get_save_response_context(
            dataset, extra_fields=['status']))

    def _put_reimport_action(self, **kwargs):
        from api.tasks import import_data
        dataset = self._get_details_query(None, None, **kwargs)
        if dataset.status not in (dataset.STATUS_IMPORTING,
                                  dataset.STATUS_UPLOADING):
            dataset.status = dataset.STATUS_IMPORTING
            dataset.save()
            import_data.delay(dataset_id=dataset.id)

        return self._render(self._get_save_response_context(
            dataset, extra_fields=['status']))

api.add_resource(DataSetResource, '/cloudml/importhandlers/\
<regex("[\w\.]*"):import_handler_id>/datasets/')
