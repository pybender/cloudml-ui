from boto.exception import S3ResponseError
from flask import request

from api import api, app
from api.amazon_utils import AmazonS3Helper
from api.base.resources import BaseResourceSQL, NotFound, \
    odesk_error_response, BaseResource
from .models import Server
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS


class ServerResource(BaseResourceSQL):
    """ Servers API methods """
    Model = Server
    ALLOWED_METHODS = ('get', )

api.add_resource(ServerResource, '/cloudml/servers/')


class ServerFileResource(BaseResource):
    """
    Amazon S3 file (model or import handler) resource.
    """
    ALLOWED_FOLDERS = [FOLDER_MODELS, FOLDER_IMPORT_HANDLERS]
    ALLOWED_METADATA_KEY_NAMES = ['name']
    PUT_ACTIONS = ('reload', )

    def _list(self, extra_params=(), **kwargs):
        server = self._get_server(kwargs)
        objects = server.list_keys(folder=self._get_folder(kwargs))
        return self._render({"%ss" % self.OBJECT_NAME: objects})

    def put(self, action=None, **kwargs):
        if action:
            return self._apply_action(action, method='PUT', **kwargs)

        server = self._get_server(kwargs)
        uid = self._get_uid(kwargs)
        folder = self._get_folder(kwargs)

        try:
            for key, val in request.form.iteritems():
                if key in self.ALLOWED_METADATA_KEY_NAMES:
                    server.set_key_metadata(uid, folder, key, val)
            from .tasks import update_at_server
            file_name = '{0}/{1}'.format(folder, uid)
            update_at_server.delay(server.id, file_name)
        except (S3ResponseError, ValueError) as err:
            status = err.status if hasattr(err, 'status') else 400
            return odesk_error_response(status, 1006, str(err))

        return self._render({self.OBJECT_NAME: {'id': uid}})

    def _put_reload_action(self, **kwargs):
        """
        Reloads model or import handler on predict.
        Needed when user manualy move it to Amazon S3.
        """
        server = self._get_server(kwargs)
        uid = self._get_uid(kwargs)
        folder = self._get_folder(kwargs)

        from .tasks import update_at_server
        file_name = '{0}/{1}'.format(folder, uid)

        update_at_server.delay(server.id, file_name)

        return self._render({self.OBJECT_NAME: {'id': uid}})

    def delete(self, action=None, **kwargs):
        server = self._get_server(kwargs)
        uid = self._get_uid(kwargs)
        folder = self._get_folder(kwargs)

        try:
            server.set_key_metadata(uid, folder, 'hide', 'True')
            from .tasks import update_at_server
            file_name = '{0}/{1}'.format(folder, uid)
            update_at_server.delay(server.id, file_name)
        except S3ResponseError as err:
            return odesk_error_response(err.status, 1006, str(err))
        return '', 204

    def _get_uid(self, kwargs):
        uid = kwargs.get('id')
        if uid is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        return uid

    def _get_folder(self, kwargs):
        folder = kwargs.get('folder')
        if folder not in self.ALLOWED_FOLDERS:
            raise NotFound(self.MESSAGE404 % kwargs)
        return folder

    def _get_server(self, kwargs):
        server_id = kwargs.get('server_id')
        if server_id is None:
            raise NotFound('Need to specify server_id')

        server = Server.query.get(server_id)
        if server is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        return server

api.add_resource(ServerFileResource,
                 '/cloudml/servers/<regex("[\w\.]*"):server_id>/\
files/<regex("[\w\.]*"):folder>/')
