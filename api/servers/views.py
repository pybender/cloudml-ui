import json

from boto.exception import S3ResponseError
from flask import request

from api import api, app
from api.amazon_utils import AmazonS3Helper
from api.base.resources import BaseResourceSQL, NotFound, \
    odesk_error_response, BaseResource
from .models import Server, ServerModelVerification, \
    XmlImportHandler, Model, VerificationExample
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS
from .forms import ServerModelVerificationForm


class ServerResource(BaseResourceSQL):
    """ Servers API methods """
    Model = Server
    GET_ACTIONS = ('models', )
    ALLOWED_METHODS = ('get', )

    def _get_models_action(self, **kwargs):
        parser_params = (('server', str), )
        params = self._parse_parameters(parser_params)
        server_id = params.get('server')
        server = Server.query.get(server_id)
        results = []
        models = server.list_keys(folder=FOLDER_MODELS)
        models_map = {item.get('name'): item for item in models}
        import_handlers = server.list_keys(folder=FOLDER_IMPORT_HANDLERS)
        handler_map = {int(item['object_id']): item
                       for item in import_handlers if item['object_id']}
        ids = handler_map.keys()
        import_handlers_obj = XmlImportHandler.query.filter(
            XmlImportHandler.id.in_(ids)).all()
        from cloudml.importhandler.importhandler import ExtractionPlan
        for h in import_handlers_obj:
            plan = ExtractionPlan(h.get_plan_config(), is_file=False)
            if plan.predict.models:
                model_name = plan.predict.models[0].value
                model_key = models_map.get(model_name)
                if model_key:
                    handler_key = handler_map[h.id]
                    model_obj = Model.query.get(model_key.get('object_id'))
                    results.append({
                        'model_name': model_name,
                        'model_metadata': model_key,
                        'model': model_obj,
                        'import_handler_name': handler_key.get('name'),
                        'import_handler': h,
                        'import_handler_metadata': handler_key
                    })
        return self._render({'files': results})


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


class ServerModelVerificationResource(BaseResourceSQL):
    """ Server Model Verifications API methods """
    Model = ServerModelVerification
    ALLOWED_METHODS = ('get', 'post', 'put')
    post_form = ServerModelVerificationForm

api.add_resource(
    ServerModelVerificationResource,
    '/cloudml/servers/verifications/')


class VerificationExampleResource(BaseResourceSQL):
    """ VerificationExample API methods """
    Model = VerificationExample
    ALLOWED_METHODS = ('get', )
    NEED_PAGING = True

    def _get_details_query(self, params, **kwargs):
        ver_example = super(VerificationExampleResource, self).\
            _get_details_query(params, **kwargs)

        if ver_example is None:
            raise NotFound()

        if not ver_example.example.is_weights_calculated:
            ver_example.example.calc_weighted_data()

        return ver_example

api.add_resource(
    VerificationExampleResource,
    '/cloudml/servers/verifications/\
<regex("[\w\.]*"):verification_id>/examples/')
