import logging
import json
from datetime import datetime

from api import celery, app
from api.import_handlers.models import ImportHandler, XmlImportHandler
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model
from api.servers.models import Server
from api.amazon_utils import AmazonS3Helper
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS


@celery.task
def upload_model_to_server(server_id, model_id, user_id):
    """
    Upload model to S3 for cloudml-predict.
    """
    init_logger('trainmodel_log', obj=int(model_id))
    logging.info('Starting uploading to cloudml_predict')

    server = Server.query.get(server_id)
    user = User.query.get(user_id)
    model = Model.query.get(model_id)

    # TODO: Shall we use another account?
    s3 = AmazonS3Helper(bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
    path = '{0}/{1}/{2}.model'.format(
        server.folder.strip('/'),
        FOLDER_MODELS,
        str(model.name)
    )
    meta = {
        'id': model.id,
        'name': model.name,
        'user_id': user.id,
        'user_name': user.name,
        'hide': "False",
        'uploaded_on': str(datetime.now())
    }

    trainer_data = model.trainer
    s3.save_key_string(path, trainer_data, meta)
    s3.close()

    logging.info('Model has been uploaded: %s' % model.name)


@celery.task
def upload_import_handler_to_server(server_id, handler_type, handler_id,
                                    user_id):
    """
    Upload importhandler to S3 for cloudml-predict.
    """
    init_logger('importdata_log', obj=int(handler_id))
    logging.info('Starting uploading to cloudml_predict')

    server = Server.query.get(server_id)
    user = User.query.get(user_id)

    _model = (XmlImportHandler if handler_type == XmlImportHandler.TYPE
              else ImportHandler)

    handler = _model.query.get(handler_id)

    # TODO: Shall we use another account?
    s3 = AmazonS3Helper(bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
    path = '{0}/{1}/{2}.{3}'.format(
        server.folder.strip('/'),
        FOLDER_IMPORT_HANDLERS,
        str(handler.name),
        'xml' if handler_type == XmlImportHandler.TYPE else 'json'
    )
    meta = {
        'id': handler.id,
        'name': handler.name,
        'type': handler.TYPE,
        'user_id': user.id,
        'user_name': user.name,
        'hide': "False",
        'uploaded_on': str(datetime.now())
    }

    handler_data = handler.get_plan_config()

    s3.save_key_string(path, handler_data, meta)
    s3.close()

    logging.info('Import Handler has been uploaded: %s' % handler.name)


@celery.task
def update_at_server(server_id, file_name):
    """
    Update given file at cloudml-predict.
    """
    import os
    import requests
    logging.info('Starting requesting cloudml_predict')

    server = Server.query.get(server_id)
    pieces = file_name.split('/')
    name = os.path.splitext(pieces[-1])[0]
    folder = pieces[-2]

    parts = {
        FOLDER_MODELS: 'model',
        FOLDER_IMPORT_HANDLERS: 'import/handler'
    }
    part = parts.get(folder)
    if not part:
        raise Exception('Wrong folder')

    url = 'http://{0}/cloudml/{1}/{2}/reload'.format(server.ip, part, name)

    logging.info(url)

    # TODO: handle response
    requests.post(url, {})

    logging.info('File has been updated: %s' % file_name)

