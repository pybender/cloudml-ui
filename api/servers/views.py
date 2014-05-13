from boto.exception import S3ResponseError
from flask import request

from api import api, app
from api.amazon_utils import AmazonS3Helper
from api.base.resources import BaseResourceSQL, NotFound, odesk_error_response, BaseResource
from .models import Server
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS


class ServerResource(BaseResourceSQL):
    """ Servers API methods """
    Model = Server
    ALLOWED_METHODS = ('get', 'options', 'put')
    GET_ACTIONS = ('list', )
    PUT_ACTIONS = ('remove', 'update_at_server', 'edit_file')

    ALLOWED_FOLDERS = [FOLDER_MODELS, FOLDER_IMPORT_HANDLERS]

    def _get_list_action(self, **kwargs):
        server = self._get_details_query(None, **kwargs)
        if server is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        path = server.folder.strip('/')
        if request.args.get('folder'):
            folder = request.args.get('folder')
            if folder in self.ALLOWED_FOLDERS:
                path += '/{0!s}'.format(folder)

        objects = []
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        for key in s3.list_keys(path):
            name = key.name.split('/')[-1]
            key = s3.bucket.get_key(key.name)
            if key.get_metadata('hide') == 'True':
                continue
            objects.append({
                'object_name': name,
                'size': key.size,
                'last_modified': key.last_modified,
                'name': key.get_metadata('name'),
                'id': key.get_metadata('id'),
                'type': key.get_metadata('type')
            })

        return self._render({self.OBJECT_NAME: {
            "%s_list" % folder: objects
        }})

    def _put_edit_file_action(self, **kwargs):
        server = self._get_details_query(None, **kwargs)
        if server is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        file_name = request.form.get('filename')
        if not file_name:
            raise NotFound(self.MESSAGE404 % kwargs)

        key = request.form.get('key')
        value = request.form.get('value')
        try:
            s3.set_key_metadata('{0}/{1}'.format(server.folder, file_name),
                                {key: value})
        except S3ResponseError as err:
            return odesk_error_response(500, 1006, str(err))

        return self._render({
            'status': 'ok'
        })

    def _put_remove_action(self, **kwargs):
        server = self._get_details_query(None, **kwargs)
        if server is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        file_name = request.form.get('filename')
        if not file_name:
            raise NotFound(self.MESSAGE404 % kwargs)

        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])

        try:
            #s3.delete_key('{0}/{1}'.format(server.folder, file_name))
            s3.set_key_metadata('{0}/{1}'.format(server.folder, file_name),
                                {'hide': "True"})
        except S3ResponseError as err:
            return odesk_error_response(500, 1006, str(err))

        return self._render({
            'status': 'ok'
        })

    def _put_update_at_server_action(self, **kwargs):
        server = self._get_details_query(None, **kwargs)
        if server is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        file_name = request.form.get('filename')
        if not file_name:
            raise NotFound(self.MESSAGE404 % kwargs)

        from .tasks import update_at_server

        update_at_server.delay(server.id, file_name)

        return self._render({
            'status': 'ok'
        })

api.add_resource(ServerResource, '/cloudml/servers/')


class ServerFileResource(BaseResource):
    ALLOWED_FOLDERS = [FOLDER_MODELS, FOLDER_IMPORT_HANDLERS]

    def _list(self, extra_params=(), **kwargs):
        server = self._get_server(kwargs)

        path = server.folder.strip('/')
        if request.args.get('folder'):
            folder = request.args.get('folder')
            if folder in self.ALLOWED_FOLDERS:
                path += '/{0!s}'.format(folder)

        objects = []
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        for key in s3.list_keys(path):
            name = key.name.split('/')[-1]
            key = s3.bucket.get_key(key.name)

            if key.get_metadata('hide') == 'True':
                continue

            objects.append({
                'id': name,
                'object_name': name,
                'size': key.size,
                'last_modified': key.last_modified,
                'name': key.get_metadata('name'),
                'object_id': key.get_metadata('id'),
                'type': key.get_metadata('type'),
                'server_id': server.id
            })

        return self._render({"%ss" % self.OBJECT_NAME: objects})

    def put(self, action=None, **kwargs):
        server = self._get_server(kwargs)

    def delete(self, action=None, **kwargs):
        server = self._get_server(kwargs)
        # TODO: delete()
        return '', 204

    def _get_server(self, kwargs):
        server_id = kwargs.get('server_id')
        if server_id is None:
            raise NotFound('Need to specify server_id')

        server = Server.query.get(server_id)
        if server is None:
            raise NotFound(self.MESSAGE404 % kwargs)
        return server

api.add_resource(ServerFileResource,
                 '/cloudml/servers/<regex("[\w\.]*"):server_id>/files/')

