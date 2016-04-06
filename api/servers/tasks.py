import logging
import json
from datetime import datetime
import base64
import uuid
import os
from celery import Task
from celery.contrib.methods import task

from models import ServerModelVerification, \
    VerificationExample, Server
from api import celery, app
from api.import_handlers.models import XmlImportHandler
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model
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


class VerifyModelTask(object):
    def run(self, verification_id, count,
            *args, **kwargs):
        self.init_logger(verification_id)

        logging.info('Starting model verification')
        self.verification = self.get_verification(verification_id)
        try:
            self.process(count)
        except Exception, exc:
            self.verification.status = self.verification.STATUS_ERROR
            self.verification.error = str(exc)
            self.verification.save()
            raise

    @property
    def importhandler(self):
        meta = self.verification.description
        if isinstance(meta, unicode):
            import json
            meta = json.loads(meta)
        if meta is None or \
                'import_handler_metadata' not in meta or \
                'name' not in meta['import_handler_metadata']:
            raise ValueError(
                "Import handler name was not specified in the metadata")
        else:
            return meta['import_handler_metadata']['name']

    def create_example_err(self, example, error, data):
        result = {
            'message': 'Error sending data to predict',
            'error': str(error),
            'status': 'Error',
            '_data': data
        }
        from urllib2 import HTTPError
        if isinstance(error, HTTPError):
            result['content'] = error.read()
        logging.error('Error: %s', result)
        ver_example = VerificationExample(
            example=example,
            verification=self.verification,
            result=result)
        ver_example.save()

    def get_config_file(self):
        import predict as predict_module
        base_path = os.path.dirname(predict_module.__file__)
        base_path = os.path.split(base_path)[0]
        env_map = {'Production': 'prod',
                   'Staging': 'staging',
                   'Development': 'dev'}
        config_file = "%s.properties" % env_map[self.verification.server.type]

        config_file = os.path.join(base_path, 'env', config_file)
        logging.info('Using %s config file', config_file)
        return config_file

    def prepare_example_data(self, example):
        data = {}
        params_map = self.verification.params_map
        if isinstance(params_map, unicode):
            import json
            params_map = json.loads(params_map)
        for k, v in params_map.iteritems():
            name = v.replace('.', '->')
            # or KeyError is expected in this case ?
            if name in example.data_input.keys():
                data[k] = example.data_input[name]
        return data

    @property
    def command(self):
        from api.base.utils import load_class
        clazz = load_class(self.verification.clazz)
        return clazz()

    @property
    def predict(self):
        from predict.libpredict import Predict
        config_file = self.get_config_file()
        predict = Predict(config_file)
        predict.cloudml_url = "http://%s/cloudml" % self.verification.server.ip
        logging.info('CloudML URL: %s', predict.cloudml_url)
        return predict

    def process(self, count):
        from api.model_tests.models import TestExample
        verification = self.verification
        results = []
        valid_count = 0
        valid_prob_count = 0
        max_time = 0
        errors_count = 0
        zero_features = verification.test_result.examples_fields

        logging.info('Using %s import handler', self.importhandler)
        logging.info('Iterating only %s test examples from %s test',
                     count, verification.test_result.name)
        examples = TestExample.query.filter_by(
            test_result=verification.test_result).limit(count)
        for example in examples:
            data = self.prepare_example_data(example)
            try:
                result = self.call_predict_command(data)
            except Exception, error:
                self.create_example_err(example, error, data)
                errors_count += 1
                continue

            # determine max response time
            if '_response_time' in result \
                    and result['_response_time'] > max_time:
                max_time = result['_response_time']
            result['_data'] = data

            # looking for zero-features
            if 'data' in result:
                for segment, features in result['data'].iteritems():
                    for feature_name, feature_value \
                            in features.iteritems():
                        if feature_name in zero_features and \
                                feature_value != 0:
                            zero_features.remove(feature_name)

            # checking whether the prediction is valid
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
            'count': count,
            'valid_prob_count': valid_prob_count,
            'max_response_time': max_time,
            'error_count': errors_count,
            'zero_features': zero_features
        }
        verification.status = verification.STATUS_DONE
        verification.save()

    def call_predict_command(self, data):
        logging.info('Sending %s to predict', data)
        if not self.verification.clazz or \
                self.verification.clazz == '- Other -':
            result = self.predict.post_to_cloudml(
                'v3', self.importhandler, None, data,
                throw_error=True, saveResponseTime=True)
        else:
            call_data = [
                'run.py',
                '-c', self.get_config_file(),
                '-i', self.importhandler,
                '-p', 'v3']
            logging.info('Calling %s command with %s',
                         self.verification.clazz, ' '.join(call_data))
            command = self.command
            parser = command.get_arg_parser()
            for key, val in data.iteritems():
                for action in parser._actions:
                    if action.dest == key:
                        opt = action.option_strings[0]
                        call_data.append(opt)
                        call_data.append(str(val))
            result = command.call(call_data)
        return result

    def init_logger(self, verification_id):
        from api.logs.models import LogMessage
        LogMessage.delete_related_logs(
            verification_id,
            type_=LogMessage.VERIFY_MODEL)
        init_logger(LogMessage.VERIFY_MODEL, obj=int(verification_id))

    def get_verification(self, verification_id):
        verification = ServerModelVerification.query.get(verification_id)
        if not verification:
            raise ValueError('Verification not found')
        verification.status = verification.STATUS_IN_PROGRESS
        verification.error = ""
        verification.result = {}
        verification.save()

        deleted_count = VerificationExample.query.filter(
            VerificationExample.verification_id == verification.id).delete(
                synchronize_session=False)
        logging.info('%s verification examples to delete', deleted_count)
        return verification


@celery.task
def verify_model(verification_id, count):
    task = VerifyModelTask()
    task.run(verification_id, count)
