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
def verify_model(verification_id, count):
    from api.logs.models import LogMessage
    from urllib2 import URLError, HTTPError

    init_logger(LogMessage.VERIFY_MODEL, obj=int(verification_id))
    LogMessage.delete_related_logs(
        verification_id,
        type_=LogMessage.VERIFY_MODEL)

    logging.info('Starting model verification')
    from models import ServerModelVerification, \
        VerificationExample
    from predict.libpredict import Predict
    verification = ServerModelVerification.query.get(verification_id)
    if not verification:
        raise ValueError('Verification not found')
    verification.status = verification.STATUS_IN_PROGRESS
    verification.error = ""
    verification.save()

    deleted_count = VerificationExample.query.filter(
        VerificationExample.verification_id == verification.id).delete(
            synchronize_session=False)
    logging.info('%s verification examples to delete', deleted_count)

    results = []
    valid_count = 0
    valid_prob_count = 0
    if 'import_handler_metadata' not in verification.description or \
            'name' not in verification.description['import_handler_metadata']:
        raise ValueError(
            "Import handler name was not specified in the metadata")

    def create_example_err(example, error, data):
        result = {
            'message': 'Error sending data to predict',
            'error': str(error),
            'status': 'Error',
            '_data': data
        }
        if isinstance(error, HTTPError):
            result['content'] = error.read()
        ver_example = VerificationExample(
            example=example,
            verification=verification,
            result=result)
        ver_example.save()

    try:
        import predict
        import os
        base_path = os.path.dirname(predict.__file__)
        base_path = os.path.split(base_path)[0]
        env_map = {'Production': 'prod',
                   'Staging': 'staging',
                   'Development': 'dev'}
        config_file = "%s.properties" % env_map[verification.server.type]

        config_file = os.path.join(base_path, 'env', config_file)
        logging.info('Using %s config file', config_file)
        predict = Predict(config_file)
        predict.cloudml_url = "http://%s/cloudml" % verification.server.ip
        logging.info('CloudML URL: %s', predict.cloudml_url)
        importhandler = verification.description['import_handler_metadata']['name']
        logging.info('Using %s import handler', importhandler)
        examples = verification.test_result.examples[:count]
        logging.info('Iterating only %s test examples from %s test',
                     count, verification.test_result.name)
        for example in examples:
            data = {}
            for k, v in verification.params_map.iteritems():
                data[k] = example.data_input[v]
            try:
                result = predict.post_to_cloudml(
                    'v3', importhandler, None, data, throw_error=True)
                result['_data'] = data
            except Exception, error:
                create_example_err(example, error, data)
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
        verification.status = verification.STATUS_DONE
        verification.save()
    except Exception, exc:
        verification.status = verification.STATUS_ERROR
        verification.error = str(exc)
        verification.save()
