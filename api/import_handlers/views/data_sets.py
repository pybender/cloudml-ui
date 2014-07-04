import os
import gzip
import json
import uuid
import re
from flask import Response, request
from sqlalchemy.orm import undefer
from psycopg2._psycopg import DatabaseError

from core.importhandler.importhandler import DecimalEncoder, \
    ImportHandlerException

from api import api
from api.base.models import assertion_msg
from api.base.resources import BaseResourceSQL, NotFound, public_actions, \
    ValidationError, odesk_error_response, ERR_INVALID_DATA
from api.import_handlers.models import DataSet
from api.import_handlers.forms import DataSetAddForm, DataSetEditForm


class DataSetResource(BaseResourceSQL):
    """
    DataSet API methods
    """
    Model = DataSet

    FILTER_PARAMS = (('status', str), )
    GET_ACTIONS = ('generate_url', 'sample_data', )
    PUT_ACTIONS = ('reupload', 'reimport')
    post_form = DataSetAddForm
    put_form = DataSetEditForm

    def _get_generate_url_action(self, **kwargs):
        ds = self._get_details_query({}, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        url = ds.get_s3_download_url()
        return self._render({self.OBJECT_NAME: ds.id,
                             'url': url})

    def _put_reupload_action(self, **kwargs):
        from api.import_handlers.tasks import upload_dataset
        dataset = self._get_details_query({}, **kwargs)
        if dataset.status == DataSet.STATUS_ERROR:
            dataset.status = DataSet.STATUS_IMPORTING
            dataset.save()
            upload_dataset.delay(dataset.id)
        return self._render({self.OBJECT_NAME: dataset})

    def _put_reimport_action(self, **kwargs):
        from api.import_handlers.tasks import import_data
        dataset = self._get_details_query({}, **kwargs)
        if dataset.status not in (DataSet.STATUS_IMPORTING,
                                  DataSet.STATUS_UPLOADING):
            dataset.status = DataSet.STATUS_IMPORTING
            dataset.save()
            import_data.delay(dataset_id=dataset.id)

        return self._render({self.OBJECT_NAME: dataset})

    def _get_sample_data_action(self, **kwargs):
        ds = self._get_details_query({}, **kwargs)
        if ds is None:
            raise NotFound('DataSet not found')
        if not os.path.exists(ds.filename):
            raise NotFound('DataSet file cannot be found')
        _, ext = os.path.splitext(ds.filename)
        open_fn = gzip.open if ext == '.gz' else open if ext == '' else None
        if not open_fn:
            raise ValidationError('DataSet has unknown file type')
        lines = []
        params = self._parse_parameters([('size', int)])
        sample_size = params.get('size') or 10
        with open_fn(ds.filename, 'rb') as f:
            line = f.readline()
            while line and len(lines) < sample_size:
                lines.append(json.loads(line))
        return self._render(lines)


api.add_resource(DataSetResource, '/cloudml/importhandlers/\
<regex("[\w\.]*"):import_handler_type>/<regex("[\w\.]*"):import_handler_id>\
/datasets/')
