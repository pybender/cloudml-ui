import logging
import json
from datetime import datetime
import base64
import uuid

from api import celery, app
from api.import_handlers.models import XmlImportHandler
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model
from api.servers.models import Server
from api.amazon_utils import AmazonS3Helper
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS


def get_a_Uuid():
    r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    return r_uuid.replace('=', '').replace('-', '')


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

    # TODO: Checking name, whether it's enough of the memory, etc.
    model_files = server.list_keys(FOLDER_MODELS)
    for file_ in model_files:
        if file_['name'] == model.name:
            raise ValueError('Model with name "{0}" already exist on '
                             'the server {1}'.format(model.name, server.name))

    uid = get_a_Uuid()

    # TODO: Shall we use another account?
    s3 = AmazonS3Helper(bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
    path = '{0}/{1}/{2}.model'.format(
        server.folder.strip('/'),
        FOLDER_MODELS,
        uid
    )
    meta = {
        'id': model.id,
        'object_name': model.name,
        'name': model.name,
        'user_id': user.id,
        'user_name': user.name,
        'hide': "False",
        'uploaded_on': str(datetime.now())
    }

    trainer_data = model.trainer
    s3.save_key_string(path, trainer_data, meta)
    s3.close()
    model.locked = True
    model.save()
    feature_set = model.features_set
    feature_set.locked = True
    feature_set.save()
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
    handler = XmlImportHandler.query.get(handler_id)

    handler_files = server.list_keys(FOLDER_IMPORT_HANDLERS)
    for file_ in handler_files:
        if file_['name'] == handler.name:
            raise ValueError('Import Handler with name "{0}" already exist on '
                             'the server {1}'.format(
                                 handler.name, server.name))

    uid = get_a_Uuid()
    # TODO: Shall we use another account?
    s3 = AmazonS3Helper(bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
    path = '{0}/{1}/{2}.{3}'.format(
        server.folder.strip('/'),
        FOLDER_IMPORT_HANDLERS,
        uid,
        'xml' if handler_type == XmlImportHandler.TYPE else 'json'
    )
    meta = {
        'id': handler.id,
        'name': handler.name,
        'object_name': handler.name,
        'type': handler.TYPE,
        'user_id': user.id,
        'user_name': user.name,
        'hide': "False",
        'uploaded_on': str(datetime.now()),
        'crc32': handler.crc32
    }

    handler_data = handler.get_plan_config()
    handler.locked = True
    handler.save()
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
        raise Exception('Wrong folder: %s' % folder)

    url = 'http://{0}/cloudml/{1}/{2}/reload'.format(server.ip, part, name)
    logging.info(url)

    # TODO: handle response
    requests.post(url, {})

    logging.info('File has been updated: %s' % file_name)


@celery.task
def verify_model(verification_id, parameters_map, count):
    from models import ServerModelVerification, \
        VerificationExample
    from predict.libpredict import Predict
    verification = ServerModelVerification.query.get(verification_id)
    if not verification:
        raise ValueError('Verification not found')
    importhandler = verification.description['import_handler_metadata']['name']
    config_file = "/home/atmel/workspace/predict-utils/env/staging.properties"
    predict = Predict(config_file)
    results = []
    valid_count = 0
    valid_prob_count = 0
    examples = verification.test_result.examples[:count + 1]
    for example in examples:
        data = {}
        for k, v in parameters_map.iteritems():
            data[k] = example.data_input[v]
        result = predict.post_to_cloudml(
            'v3', importhandler, None, data)
        if result is None:
            continue

        if 'raw_data' in result:
            del result['raw_data']
        if 'prediction' in result and \
                result['prediction'] == example.pred_label:
            valid_count += 1
            if 'result' in result and 'probability' in result['result']:
                def approximately_equal(val1, val2, accuracy=4):
                    return round(val1, accuracy) == round(val2, accuracy)

                example_prob = max(example.prob)
                prob = result['result']['probability']
                if approximately_equal(example_prob, prob):
                    valid_prob_count += 1

        ver_example = VerificationExample(
            example=example,
            verification=verification,
            result=result)
        ver_example.save()
    verification.result = {
        'valid_count': valid_count,
        'count': len(examples),
        'valid_prob_count': valid_prob_count
    }
    verification.save()
