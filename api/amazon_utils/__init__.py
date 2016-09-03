"""
Amazon services helper classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import S3Transfer, TransferConfig
import urllib

from api import app
from api.base.exceptions import ApiBaseException


class AmazonS3ObjectNotFound(ApiBaseException):
    pass


class S3ResponseError(ApiBaseException):
    pass


class AmazonMixin(object):
    """
    This class keeps amazon settings
    """
    def __init__(self, token=None, secret=None):
        self.token = token or app.config['AMAZON_ACCESS_TOKEN']
        self.secret = secret or app.config['AMAZON_TOKEN_SECRET']


class AmazonEMRHelper(AmazonMixin):
    """
    This class provies an interface to the Elastic MapReduce (EMR)
    service from AWS.
    """
    def __init__(self, token=None, secret=None, region='us-west-1'):
        super(AmazonEMRHelper, self).__init__(token, secret)
        self.conn = boto3.client('emr',
                                 region_name=region,
                                 aws_access_key_id=self.token,
                                 aws_secret_access_key=self.secret)

    def terminate_jobflow(self, jobflowid):
        """
        Terminate an Elastic MapReduce job flow

        jobflow_id: str
            A jobflow id
        """
        return self.conn.terminate_job_flows(JobFlowIds=[jobflowid])

    def describe_jobflow(self, jobflowid):
        """
        Describes a single Elastic MapReduce job flow

        jobflow_id: str
            The job flow id of interest
        """
        return self.conn.describe_job_flows(
            JobFlowIds=[jobflowid])['JobFlows'][0]


class AmazonEC2Helper(AmazonMixin):
    """
    Class provides an interface to the Elastic Compute Cloud (EC2)
    service from AWS.
    """
    def __init__(self, token=None, secret=None, region='us-west-2'):
        super(AmazonEC2Helper, self).__init__(token, secret)
        self.resource = boto3.resource('ec2',
                                       region_name=region,
                                       aws_access_key_id=self.token,
                                       aws_secret_access_key=self.secret)
        self.client = self.resource.meta.client

    def terminate_instance(self, instance_id):
        """
        Terminates the specified instance.

        instance_id: str
            The ID of the instance to be terminated.
        """
        return self.client.terminate_instances(
            InstanceIds=[instance_id, ])

    def request_spot_instance(self, instance_type='m3.xlarge'):
        """
        Request instances on the spot market.

        instance_type: string
            The type of instance to run:
                * t1.micro
                * m1.small
                * m1.medium
                * m1.large
                * m1.xlarge
                * m3.medium
                * m3.large
                * m3.xlarge
                * m3.2xlarge
                * c1.medium
                * c1.xlarge
                * m2.xlarge
                * m2.2xlarge
                * m2.4xlarge
                * cr1.8xlarge
                * hi1.4xlarge
                * hs1.8xlarge
                * cc1.4xlarge
                * cg1.4xlarge
                * cc2.8xlarge
                * g2.2xlarge
                * c3.large
                * c3.xlarge
                * c3.2xlarge
                * c3.4xlarge
                * c3.8xlarge
                * i2.xlarge
                * i2.2xlarge
                * i2.4xlarge
                * i2.8xlarge
                * t2.micro
                * t2.small
                * t2.medium

        Note
        ----
        previously used amis: ami-4e36567e,ami-14c05a24,ami-68c85358
        ami-a068f590,ami-78b42948,ami-65821055,ami-a7f96b97,ami-f0af86b5
        ami-66c8e123
        subnet: subnet-3f5bc256
        security_group_ids: sg-534f5d3f
        """
        request = self.client.request_spot_instances(
            SpotPrice="1",
            LaunchSpecification={
                'ImageId': 'ami-71d49241',
                'InstanceType': instance_type,
                'Placement': {'AvailabilityZone': "us-west-2a"},
                'SubnetId': 'subnet-7a7c3612',
                'SecurityGroupIds': ['sg-1dc1dc71']
            })
        return request['SpotInstanceRequests'][0]

    def get_instance(self, instance_id):
        """
        Retrieve the instance reservations by instance_id.
        """
        return self.resource.Instance(instance_id)

    def get_request_spot_instance(self, request_id):
        """
        Retrieve the spot instances request by request_id.

        request_id: str
            The Request ID
        """
        requests = self.client.describe_spot_instance_requests(
            SpotInstanceRequestIds=[request_id, ])
        return requests['SpotInstanceRequests'][0]

    def cancel_request_spot_instance(self, request_id):
        """
        Cancel the specified Spot Instance Request.

        request_id: str
            The Request ID to terminate
        """
        request = self.client.cancel_spot_instance_requests(
            SpotInstanceRequestIds=[request_id, ])
        return request['CancelledSpotInstanceRequests'][0]


class AmazonS3Helper(AmazonMixin):
    """
    Class provides an interface to the Simple Storage Service
    service from Amazon.
    """
    def __init__(self, token=None, secret=None, bucket_name=None):
        super(AmazonS3Helper, self).__init__(token, secret)
        self.bucket_name = bucket_name or app.config['AMAZON_BUCKET_NAME']
        self.conn = boto3.resource('s3',
                                   aws_access_key_id=self.token,
                                   aws_secret_access_key=self.secret)

    def get_download_url(self, name, expires_in):
        """
        Generate a URL to access this key.

        name: string
            name of the key
        expires_in: int
            How long the url is valid for, in seconds
        """
        url = self.conn.meta.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': name},
            ExpiresIn=expires_in)
        return url

    def list_keys(self, prefix):
        """
        List key objects within a bucket.

        prefix: string
            allows you to limit the listing to a particular
            prefix.  For example, if you call the method with
            prefix='/foo/' then the iterator will only cycle through
            the keys that begin with the string '/foo/'.
        """
        res = self.conn.meta.client.list_objects(Bucket=self.bucket_name,
                                                 Prefix=prefix)
        return res.get('Contents', [])

    def load_key(self, name, with_metadata=False):
        """
        Retrieve an object from S3 using the name of the Key object as the
        key in S3.  Return the contents of the object as a string.

        name: string
            name of the key
        """
        n = 0
        while n < 4:
            try:
                res = self.conn.Object(self.bucket_name, name).get()
                if with_metadata:
                    metadata = {}
                    for meta_k, meta_v in res['Metadata'].iteritems():
                        metadata[meta_k] = urllib.unquote(meta_v).\
                            decode('utf8')
                    res['Metadata'] = metadata
                    return res
                return res['Body'].read(res['ContentLength'])
            except Exception, exc:
                logging.info('Got error %s try again for %s' % (exc, name))
                n += 1
                logging.error('Got error when getting data from s3')

        raise AmazonS3ObjectNotFound("Object %s doesn't exist on S3" % name)

    def save_gz_file(self, name, filename, meta={}):
        """
        Saves file to Amazon S3 using multipart upload.

        name: string
            Amazon S3 key name
        filename: string
            The name of the file that you want to put onto S3
        meta: dict
            Additional metadata, should be setted to the Key
        """
        config = TransferConfig(
            multipart_threshold=app.config.get('MULTIPART_UPLOAD_CHUNK_SIZE'))
        transfer = S3Transfer(self.conn.meta.client, config)
        return transfer.upload_file(
            filename, self.bucket_name, name,
            extra_args={'ContentType': 'application/octet-stream',
                        'ContentEncoding': 'gzip',
                        'Metadata': self._prepare_meta(meta)})

    def save_key(self, name, filename, meta={}, compressed=True):
        """
        Store an object in S3 using the name of the Key object as the
        key in S3 and the contents of the file named by 'filename'.

        name: string
            Amazon S3 key name
        filename: string
            The name of the file that you want to put onto S3
        meta: dict
            Additional metadata, should be setted to the Key
        compressed: bool
            True, if the file is compressed (gzip). Otherwise, False.
        """
        kwargs = {'Body': open(filename, 'rb'),
                  'Metadata': self._prepare_meta(meta),
                  'ContentType': 'application/octet-stream'}
        if compressed:
            kwargs['ContentEncoding'] = 'gzip'
        return self.conn.Object(self.bucket_name, name).put(**kwargs)

    def save_key_string(self, name, data, meta={}):
        """
        Store an object in S3 using the name of the Key object as the
        key in S3 and the string 's' as the contents.

        name: string
            Amazon S3 key name
        data: string
            The data to be saved to Amazon S3 key.
        meta: dict
            Additional metadata, should be setted to the Key
        """
        return self.conn.Object(self.bucket_name, name).put(
            Body=data,
            Metadata=self._prepare_meta(meta))

    def set_key_metadata(self, name, meta, store_previous=False):
        """
        Updates the metadata of the specified key.

        name: string
            Amazon S3 key name
        meta: dict
            The metadata, should be setted to the Key
        store_previous: bool
            Determines whether we need to save previous metadata with prefix
            "previous_".
        """
        if not self.key_exists(name):
            raise AmazonS3ObjectNotFound("Key '{}' not found".format(name))
        resp = self.conn.Object(self.bucket_name, name).get()
        metadata = resp.get('Metadata', {})
        for meta_key, meta_val in meta.iteritems():
            if store_previous:
                previous_value = metadata.get(meta_key, '')
                metadata["previous_"+meta_key] = str(previous_value)
            metadata[meta_key] = str(meta_val)
        return self.conn.Object(self.bucket_name, name).copy_from(
            Metadata=metadata,
            MetadataDirective='REPLACE',
            CopySource='%s/%s' % (self.bucket_name, name))

    def delete_key(self, name):
        """
        Delete the key from S3

        name: string
            Amazon S3 key name
        """
        return self.conn.Object(self.bucket_name, name).delete()

    def close(self):
        pass

    def _check_or_create_bucket(self):
        """
        Checks if the bucket exists on Amazon S3 (by bucket_name).
        Creates the one, if it doesn't exists.
        """
        try:
            self.conn.meta.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                # bucket doesn't exist - create new one
                self.conn.Bucket(self.bucket_name).create()
            else:
                raise S3ResponseError(e.message, e)
        return True

    def key_exists(self, name):
        """
        Checks if key exists in the bucket
        """
        try:
            self.conn.Object(self.bucket_name, name).load()
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise S3ResponseError(e.message, e)

    def _prepare_meta(self, meta):
        for key, val in meta.iteritems():
            meta[key] = str(val)
        return meta


class AmazonDynamoDBHelper(AmazonMixin):
    """
    Class provides an interface to the NoSQL database Amazon DynamoDB2.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AmazonDynamoDBHelper, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self, token=None, secret=None):
        super(AmazonDynamoDBHelper, self).__init__(token, secret)
        self._conn = None
        self.resource = None
        self._tables = {}

    @property
    def conn(self):
        if not self._conn:
            if app.config.get('TEST_DYNAMODB'):
                self.resource = boto3.resource(
                    'dynamodb',
                    aws_access_key_id='ak',
                    aws_secret_access_key='sk',
                    region_name='us-west-2')
            elif app.config.get('LOCAL_DYNAMODB'):
                # Local DynamoDB (see dynamodb_local.sh)
                self.resource = boto3.resource(
                    'dynamodb',
                    aws_access_key_id='any',
                    aws_secret_access_key='any',
                    endpoint_url='http://localhost:8000',
                    region_name='us-west-2')
            else:
                # Real DynamoDB connection
                self.resource = boto3.resource(
                    'dynamodb',
                    aws_access_key_id=self.token,
                    aws_secret_access_key=self.secret,
                    region_name='us-west-1')
            self._conn = self.resource.meta.client
        return self._conn

    def _get_table(self, table_name):
        if table_name not in self._tables:
            self._refresh_tables_list()

        return self._tables[table_name]

    def _refresh_tables_list(self):
        self._tables = {}
        start_table = None
        while True:
            kwargs = {'Limit': 50}
            if start_table:
                kwargs['ExclusiveStartTableName'] = start_table
            result = self.conn.list_tables(**kwargs)
            start_table = result.get('LastEvaluatedTableName', None)
            for table_name in result['TableNames']:
                table = self.resource.Table(table_name)
                self.conn.describe_table(TableName=table_name)
                self._tables[table_name] = table
            if not start_table:
                break

    def put_item(self, table_name, data):
        """
        Saves an entire item to DynamoDB table.

        table_name: string
            Name of the table
        data: dict
            A dictionary of the data you'd like to store in DynamoDB.
        """
        table = self._get_table(table_name)
        return table.put_item(Item=data)

    def delete_items(self, table_name, keys, **kwargs):
        table = self._get_table(table_name)
        res = table.query(**kwargs)
        with table.batch_writer() as batch:
            for item in res['Items']:
                k = {}
                for key in keys:
                    k[key] = item[key]
                batch.delete_item(Key=k)

    def delete_item(self, table_name, **kwargs):
        """
        Deletes a single item. You can perform a conditional delete operation
        that deletes the item if it exists, or if it has an expected attribute
        value.
        """
        table = self._get_table(table_name)
        return table.delete_item(Key=kwargs)

    def batch_write(self, table_name, data_list):
        table = self._get_table(table_name)
        with table.batch_writer() as batch:
            for data in data_list:
                batch.put_item(Item=data)

    def get_item(self, table_name, **kwargs):
        """
        Fetches an item (record) from a table in DynamoDB.
        To specify the key of the item you'd like to get, you can specify the
        key attributes as kwargs.

        Returns an ``Item`` instance containing all the data for that record.
        """
        table = self._get_table(table_name)
        item = table.get_item(Key=kwargs)
        return item.get('Item', None)

    def get_items(self, table_name, **kwargs):
        table = self._get_table(table_name)
        res = table.query(**kwargs)
        return res['Items']

    def create_table(self, table_name, schema, types):
        """
        Creates a new table in DynamoDB & returns an
        in-memory ``Table`` object.
        """
        self._refresh_tables_list()
        if table_name not in self._tables:
            try:
                self.conn.create_table(
                    TableName=table_name, KeySchema=schema,
                    AttributeDefinitions=types,
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 10000,
                        'WriteCapacityUnits': 10000
                    }
                )
                self._tables[table_name] = self.resource.Table(table_name)
            except ClientError as ex:
                logging.exception(str(ex))


def amazon_config():
    """
    Returns amazon credentials of current config
    """
    return app.config['AMAZON_ACCESS_TOKEN'], \
        app.config['AMAZON_TOKEN_SECRET'], \
        app.config['AMAZON_BUCKET_NAME']
