""" Spot instances tasks """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
from botocore.exceptions import ClientError
from os import system, popen

from api import celery, app
from api.logs.logger import init_logger
from api.amazon_utils import AmazonEC2Helper
from api.ml_models.models import Model
from api.base.tasks import SqlAlchemyTask
from api.instances.models import Cluster
from api.amazon_utils import AmazonEMRHelper


class InstanceRequestingError(Exception):
    pass


@celery.task(base=SqlAlchemyTask)
def synchronyze_cluster_list():
    """
    Updates cluster's statuses.
    """
    clusters = Cluster.query.all()
    emr = AmazonEMRHelper()
    for cluster in clusters:
        status = emr.describe_jobflow(
            cluster.jobflow_id)['ExecutionStatusDetail']['State'].lower()
        if status == 'terminated':
            logging.info('Cluster %s terminated, it will be deleted'
                         % cluster.jobflow_id)
            cluster.delete()
        if status in Cluster.STATUSES:
            cluster.status = status
            cluster.save()
        else:
            logging.info('Unknown jobflow status %s' % status)


@celery.task(base=SqlAlchemyTask)
def request_spot_instance(instance_type=None, model_id=None):
    """
    Requests instance on the Amazon spot market.

    instance_type: string
        The type of instance to run.
    model_id: int
        Id of the Model which tries to request spot instance
        for training.
    """
    init_logger('trainmodel_log', obj=int(model_id))

    model = Model.query.get(model_id)
    model.status = model.STATUS_REQUESTING_INSTANCE
    model.save()

    try:
        ec2 = AmazonEC2Helper()
        logging.info('Request spot instance type: %s' % instance_type)
        request = ec2.request_spot_instance(instance_type)
        logging.info('Request id: %s:' % request['SpotInstanceRequestId'])
    except ClientError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)

    model.spot_instance_request_id = request['SpotInstanceRequestId']
    model.save()

    return request['SpotInstanceRequestId']


@celery.task(base=SqlAlchemyTask)
def get_request_instance(request_id, callback=None, dataset_ids=None,
                         model_id=None, user_id=None):
    """
    Tries to get requested spot instance from Amazon EC2.
    Dependly of the instance state it fills instance fields or retries
    the task, if instance is opening.

    request_id: string
        The spot instance request ID.
    callback: string
        If `train` specified, system will run model training after the spot
        instance would be launched.
    dataset_ids: list of integers
        List of dataset ids used for model training.
    model_id: int
        Id of the model to train on this spot instance.
    user_id: int
        Id of the user, who initiate training the model.

    Note:
        dataset_ids, model_id, user_id should be specified
        when callback is `train`.
    """
    init_logger('trainmodel_log', obj=int(model_id))
    ec2 = AmazonEC2Helper()
    logging.info('Get spot instance request %s' % request_id)

    model = Model.query.get(model_id)
    try:
        request = ec2.get_request_spot_instance(request_id)
    except ClientError as e:
        model.set_error(e.error_message)
        raise InstanceRequestingError(e.error_message)

    if request['State'] == 'open':
        logging.info('Instance was not ran. \
Status: %s . Retry in 10s.' % request['State'])
        try:
            raise get_request_instance.retry(
                countdown=app.config['REQUESTING_INSTANCE_COUNTDOWN'],
                max_retries=app.config['REQUESTING_INSTANCE_MAX_RETRIES'])
        except get_request_instance.MaxRetriesExceededError:
            logging.info('Max retries was reached, cancelling now.')
            cancel_request_spot_instance.delay(request_id, model_id)
            model.set_error('Instance was not launched')
            raise InstanceRequestingError('Instance was not launched')

    if request['State'] == 'canceled':
        logging.info('Instance was canceled.')
        model.status = model.STATUS_CANCELED
        model.save()
        return None

    if request['State'] != 'active':
        logging.info('Instance was not launched. \
State is {0!s}, status is {1!s}, {2!s}.'.format(
            request['State'], request['Status']['Code'],
            request['Status']['Message']))
        model.set_error('Instance was not launched')
        raise InstanceRequestingError('Instance was not launched')

    model.status = model.STATUS_INSTANCE_STARTED
    model.save()

    logging.info('Get instance %s' % request['InstanceId'])
    instance = ec2.get_instance(request['InstanceId'])
    logging.info('Instance %s(%s) lunched' %
                 (instance.id, instance.private_ip_address))
    tags = [{'Key': 'Name', 'Value': 'cloudml-worker-auto'},
            {'Key': 'Owner', 'Value': 'papadimitriou,nmelnik'},
            {'Key': 'Model_id', 'Value': str(model_id)},
            {'Key': 'whoami', 'Value': 'cloudml'}]
    instance.create_tags(Tags=tags)

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


@celery.task(base=SqlAlchemyTask)
def terminate_instance(instance_id=None):
    """
    Terminates Amazon EC2 instance.

    instance_id: str
        The ID of the instance to be terminated.
    """
    ec2 = AmazonEC2Helper()
    ec2.terminate_instance(instance_id)
    logging.info('Instance %s terminated' % instance_id)


@celery.task(base=SqlAlchemyTask)
def self_terminate(result=None):  # pragma: no cover
    logging.info('Instance will be terminated')
    system("halt")


@celery.task(base=SqlAlchemyTask)
def cancel_request_spot_instance(request_id, model_id):
    """
    Cancel the specified Spot Instance Request.

    request_id: str
        The Request ID to terminate
    model_id: int
        Id of the Model which requested the spot instance
        for training.
    """
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
    except ClientError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)


@celery.task(base=SqlAlchemyTask)
def run_ssh_tunnel(cluster_id):
    """
    Creates SSH tunnel to the cluster for getting access to Hadoop Web UI.

    cluster_id: int
        Id of the cluster
    """
    from api.instances.models import Cluster
    import subprocess
    import shlex
    cluster = Cluster.query.get(cluster_id)
    try:
        ssh_command = "ssh -o StrictHostKeyChecking=no -g -L %(port)d:%(dns)s:\
9026 hadoop@%(dns)s -i /home/cloudml/.ssh/cloudml-control.pem" \
            % {"dns": cluster.master_node_dns, "port": cluster.port}
        args = shlex.split(ssh_command)
        p = subprocess.Popen(args, shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        cluster.pid = p.pid
        cluster.save()
        for line in p.stdout.readlines():
            logging.info(line)
        retval = p.wait()
    except:
        cluster.pid = None
        cluster.save()
