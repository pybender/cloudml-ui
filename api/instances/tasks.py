""" Spot instances tasks """
import logging
from boto.exception import EC2ResponseError
from os import system

from api import celery, app
from api.logs.logger import init_logger
from api.amazon_utils import AmazonEC2Helper
from api.ml_models.models import Model


class InstanceRequestingError(Exception):
    pass


@celery.task
def request_spot_instance(dataset_id=None, instance_type=None, model_id=None):
    init_logger('trainmodel_log', obj=int(model_id))

    model = Model.query.get(model_id)
    model.status = model.STATUS_REQUESTING_INSTANCE
    model.save()

    try:
        ec2 = AmazonEC2Helper()
        logging.info('Request spot instance type: %s' % instance_type)
        request = ec2.request_spot_instance(instance_type)
        logging.info('Request id: %s:' % request.id)
    except EC2ResponseError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)

    model.spot_instance_request_id = request.id
    model.save()

    return request.id


@celery.task()
def get_request_instance(request_id,
                         callback=None,
                         dataset_ids=None,
                         model_id=None,
                         user_id=None):
    init_logger('trainmodel_log', obj=int(model_id))
    ec2 = AmazonEC2Helper()
    logging.info('Get spot instance request %s' % request_id)

    model = Model.query.get(model_id)

    try:
        request = ec2.get_request_spot_instance(request_id)
    except EC2ResponseError as e:
        model.set_error(e.error_message)
        raise InstanceRequestingError(e.error_message)

    if request.state == 'open':
        logging.info('Instance was not ran. \
Status: %s . Retry in 10s.' % request.state)
        try:
            raise get_request_instance.retry(
                countdown=app.config['REQUESTING_INSTANCE_COUNTDOWN'],
                max_retries=app.config['REQUESTING_INSTANCE_MAX_RETRIES'])
        except get_request_instance.MaxRetriesExceededError:
            logging.info('Max retries was reached, cancelling now.')
            cancel_request_spot_instance.delay(request_id, model_id)
            model.set_error('Instance was not launched')
            raise InstanceRequestingError('Instance was not launched')

    if request.state == 'canceled':
        logging.info('Instance was canceled.')
        model.status = model.STATUS_CANCELED
        model.save()
        return None

    if request.state != 'active':
        logging.info('Instance was not launched. \
State is {0!s}, status is {1!s}, {2!s}.'.format(
            request.state, request.status.code, request.status.message))
        model.set_error('Instance was not launched')
        raise InstanceRequestingError('Instance was not launched')

    model.status = model.STATUS_INSTANCE_STARTED
    model.save()

    logging.info('Get instance %s' % request.instance_id)
    instance = ec2.get_instance(request.instance_id)
    logging.info('Instance %s(%s) lunched' %
                 (instance.id, instance.private_ip_address))
    instance.add_tag('Name', 'cloudml-worker-auto')
    instance.add_tag('Owner', 'papadimitriou,nmelnik')
    instance.add_tag('Model_id', model_id)
    instance.add_tag('whoami', 'cloudml')

    if callback == "train":
        logging.info('Train model task apply async')
        queue = "ip-%s" % "-".join(instance.private_ip_address.split('.'))
        from api.ml_models.tasks import train_model
        train_model.apply_async(
            (dataset_ids, model_id, user_id),
            queue=queue,
            link=terminate_instance.subtask(
                kwargs={'instance_id': instance.id}),
            link_error=terminate_instance.subtask(
                kwargs={'instance_id': instance.id}))
    return instance.private_ip_address


@celery.task
def terminate_instance(task_id=None, instance_id=None):
    ec2 = AmazonEC2Helper()
    ec2.terminate_instance(instance_id)
    logging.info('Instance %s terminated' % instance_id)


@celery.task
def self_terminate(result=None):  # pragma: no cover
    logging.info('Instance will be terminated')
    system("halt")


@celery.task
def cancel_request_spot_instance(request_id, model_id):
    init_logger('trainmodel_log', obj=int(model_id))
    model = Model.query.get(model_id)

    logging.info('Cancelling spot instance request {0!s} \
for model id {1!s}...'.format(
        request_id, model_id))

    try:
        AmazonEC2Helper().cancel_request_spot_instance(request_id)
        logging.info('Spot instance request {0!s} has been \
cancelled for model id {1!s}'.format(request_id, model_id))
        model.status = model.STATUS_CANCELED
        model.save()
    except EC2ResponseError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)
