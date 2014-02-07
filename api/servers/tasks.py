import logging
import json
from api.amazon_utils import AmazonS3Helper
from datetime import datetime

from api import celery, app
from api.import_handlers.models import ImportHandler
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model
from api.servers.models import Server


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
    path = '{0}/models/{1}.model'.format(
        server.folder.strip('/'),
        str(model.name)
    )
    meta = {
        'model_id': model.id,
        'model_name': model.name,
        'user_id': user.id,
        'user_name': user.name,
        'uploaded_on': str(datetime.now())
    }

    trainer_data = model.trainer
    s3.save_key_string(path, trainer_data, meta)
    s3.close()

    logging.info('Model has been uploaded: %s' % model.name)


@celery.task
def upload_import_handler_to_server(server_id, handler_id, user_id):
    """
    Upload importhandler to S3 for cloudml-predict.
    """
    init_logger('importdata_log', obj=int(handler_id))
    logging.info('Starting uploading to cloudml_predict')

    server = Server.query.get(server_id)
    user = User.query.get(user_id)
    handler = ImportHandler.query.get(handler_id)

    # TODO: Shall we use another account?
    s3 = AmazonS3Helper(bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
    path = '{0}/models/{1}.json'.format(
        server.folder.strip('/'),
        str(handler.name)
    )
    meta = {
        'handler_id': handler.id,
        'handler_name': handler.name,
        'user_id': user.id,
        'user_name': user.name,
        'uploaded_on': str(datetime.now())
    }

    handler_data = json.dumps(handler.data)
    s3.save_key_string(path, handler_data, meta)
    s3.close()

    logging.info('Import Handler has been uploaded: %s' % handler.name)
