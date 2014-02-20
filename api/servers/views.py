from boto.exception import S3ResponseError
from flask import request

from api import api, app
from api.amazon_utils import AmazonS3Helper
from api.base.resources import BaseResourceSQL, NotFound, odesk_error_response
from models import Server


class ServerResource(BaseResourceSQL):
    """ Servers API methods """
    Model = Server
    ALLOWED_METHODS = ('get', 'options', 'put')
    GET_ACTIONS = ('list',)
    PUT_ACTIONS = ('remove',)

    ALLOWED_FOLDERS = ['models', 'importhandlers']

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
            objects.append({
                'name': name,
                'size': key.size,
                'last_modified': key.last_modified
            })

        return self._render({
            'list': objects
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
            s3.delete_key('{0}/{1}'.format(server.folder, file_name))
        except S3ResponseError as err:
            return odesk_error_response(500, 1006, str(err))

        return self._render({
            'status': 'ok'
        })

api.add_resource(ServerResource, '/cloudml/servers/')
