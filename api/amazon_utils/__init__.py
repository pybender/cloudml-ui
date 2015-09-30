"""
Amazon services helper classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import uuid
from boto.dynamodb2.table import Table

import boto.ec2
from boto.exception import JSONResponseError
from boto.s3.key import Key

from api import app


class AmazonEMRHelper(object):
    """
    This class provies an interface to the Elastic MapReduce (EMR)
    service from AWS.
    """
    def __init__(self, token=None, secret=None, region='us-west-1'):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.conn = boto.emr.connect_to_region(
            region,
            aws_access_key_id=token,
            aws_secret_access_key=secret)

    def terminate_jobflow(self, jobflowid):
        """
        Terminate an Elastic MapReduce job flow

        jobflow_id: str
            A jobflow id
        """
        self.conn.terminate_jobflow(jobflowid)

    def describe_jobflow(self, jobflowid):
        """
        Describes a single Elastic MapReduce job flow

        jobflow_id: str
            The job flow id of interest
        """
        return self.conn.describe_jobflow(jobflowid)


class AmazonEC2Helper(object):
    """
    Class provides an interface to the Elastic Compute Cloud (EC2)
    service from AWS.
    """
    def __init__(self, token=None, secret=None, region='us-west-2'):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.conn = boto.ec2.connect_to_region(
            region,
            aws_access_key_id=token,
            aws_secret_access_key=secret)

    def terminate_instance(self, instance_id):
        """
        Terminates the specified instance.

        instance_id: str
            The ID of the instance to be terminated.
        """
        return self.conn.terminate_instances(
            instance_ids=[instance_id, ])

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
        request = self.conn.request_spot_instances(
            price="1",
            image_id='ami-71d49241',
            security_group_ids=["sg-1dc1dc71"],
            instance_type=instance_type,
            placement="us-west-2a",
            subnet_id="subnet-7a7c3612")
        return request[0]

    def get_instance(self, instance_id):
        """
        Retrieve the instance reservations by instance_id.
        """
        reservations = self.conn.get_all_instances(
            instance_ids=[instance_id, ])
        instance = reservations[0].instances[0]
        return instance

    def get_request_spot_instance(self, request_id):
        """
        Retrieve the spot instances request by request_id.

        request_id: str
            The Request ID
        """
        request = self.conn.get_all_spot_instance_requests(
            request_ids=[request_id, ])
        request = request[0]
        return request

    def cancel_request_spot_instance(self, request_id):
        """
        Cancel the specified Spot Instance Request.

        request_id: str
            The Request ID to terminate
        """
        request = self.conn.cancel_spot_instance_requests([request_id, ])
        request = request[0]
        return request


class AmazonS3Helper(object):
    """
    Class provides an interface to the Simple Storage Service
    service from Amazon.
    """
    def __init__(self, token=None, secret=None, bucket_name=None):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.bucket_name = bucket_name or app.config['AMAZON_BUCKET_NAME']
        self.conn = boto.connect_s3(token, secret)

    @property
    def bucket(self):
        """
        Returns Amazon S3 bucket.
        """
        if not hasattr(self, '_bucket'):
            self._bucket = self._get_bucket()
        return self._bucket

    def get_download_url(self, name, expires_in):
        """
        Generate a URL to access this key.

        name: string
            name of the key
        expires_in: int
            How long the url is valid for, in seconds
        """
        key = Key(self.bucket)
        key.key = name
        return key.generate_url(expires_in)

    def list_keys(self, prefix):
        """
        List key objects within a bucket.

        prefix: string
            allows you to limit the listing to a particular
            prefix.  For example, if you call the method with
            prefix='/foo/' then the iterator will only cycle through
            the keys that begin with the string '/foo/'.
        """
        return self.bucket.list(prefix)

    def load_key(self, name):
        """
        Retrieve an object from S3 using the name of the Key object as the
        key in S3.  Return the contents of the object as a string.

        name: string
            name of the key
        """
        key = Key(self.bucket)
        key.key = name
        n = 0
        try:
            return key.get_contents_as_string()
        except Exception, exc:
            if n < 4:
                logging.info('Got error %s try again %d' % (name, n))
                n += 1
            else:
                logging.error('Got error when getting data from s3')
                raise exc

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
        import cStringIO

        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Encoding': 'gzip'
        }
        mpu = self.bucket.initiate_multipart_upload(
            name,
            metadata=meta,
            headers=headers
        )
        stream = cStringIO.StringIO()
        part_count = [0]

        def progress(x, y):
            if y > 0:
                logging.debug(
                    "Part %d: %0.2f%%" % (part_count[0], 100. * x / y))

        def upload_part(part_count=[0]):
            part_count[0] += 1
            stream.seek(0)
            mpu.upload_part_from_file(stream, part_count[0], cb=progress)
            stream.seek(0)
            stream.truncate()

        with open(filename, 'r') as input_file:
            while True:
                chunk = input_file.read(
                    app.config.get('MULTIPART_UPLOAD_CHUNK_SIZE'))
                if len(chunk) == 0:
                    upload_part(part_count)
                    logging.info('Uploaded parts: {0!s}'.format(
                        [(part.part_number, part.size) for part in mpu]))
                    mpu.complete_upload()
                    break
                stream.write(chunk)
                if stream.tell() > 5 * 1024 * 1024:
                    upload_part(part_count)

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
        key = Key(self.bucket)
        key.key = name
        for meta_key, meta_val in meta.iteritems():
            key.set_metadata(meta_key, meta_val)

        headers = {'Content-Type': 'application/octet-stream'}
        if compressed:
            headers['Content-Encoding'] = 'gzip'
        key.set_contents_from_filename(filename, headers)

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
        key = Key(self.bucket)
        key.key = name
        for meta_key, meta_val in meta.iteritems():
            key.set_metadata(meta_key, meta_val)
        key.set_contents_from_string(data)

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
        key = self.bucket.lookup(name)
        for meta_key, meta_val in meta.iteritems():
            if store_previous:
                previous_value = key.get_metadata(meta_key)
                key.set_metadata("previous_" + meta_key, previous_value)
            key.set_metadata(meta_key, meta_val)
        # key.metadata.update(meta)
        key.copy(key.bucket.name, key.name, key.metadata)

    def delete_key(self, name):
        """
        Delete the key from S3

        name: string
            Amazon S3 key name
        """
        key = Key(self.bucket)
        key.key = name
        key.delete()

    def close(self):
        pass

    def _get_bucket(self):
        """
        Gets the bucket on Amazon S3 by bucket_name.
        Creates the one, if it doesn't exists.
        """
        bucket = self.conn.lookup(self.bucket_name)
        if bucket is None:
            bucket = self.conn.create_bucket(self.bucket_name)
        return bucket


class AmazonDynamoDBHelper(object):
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
        self.token = token or app.config['AMAZON_ACCESS_TOKEN']
        self.secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self._conn = None
        self._tables = {}

    @property
    def conn(self):
        if not self._conn:
            from boto import dynamodb2
            from boto.dynamodb2.layer1 import DynamoDBConnection

            if app.config.get('TEST_DYNAMODB'):
                self._conn = boto.dynamodb2.connect_to_region(
                    'us-west-2', aws_access_key_id="ak",
                    aws_secret_access_key="sk")
            elif app.config.get('LOCAL_DYNAMODB'):
                # Local DynamoDB (see dynamodb_local.sh)
                self._conn = DynamoDBConnection(
                    host='localhost',
                    port=8000,
                    aws_access_key_id='any',
                    aws_secret_access_key='any',
                    is_secure=False)
            else:
                # Real DynamoDB connection
                self._conn = dynamodb2.connect_to_region(
                    'us-west-1',
                    aws_access_key_id=self.token,
                    aws_secret_access_key=self.secret)
        return self._conn

    def _get_table(self, table_name):
        if table_name not in self._tables:
            self._refresh_tables_list()

        return self._tables[table_name]

    def _refresh_tables_list(self):
        from boto.dynamodb2.table import Table
        self._tables = {}
        for table_name in self.conn.list_tables()['TableNames']:
            table = Table(table_name, connection=self.conn)
            table.describe()
            self._tables[table_name] = table

    def put_item(self, table_name, data):
        """
        Saves an entire item to DynamoDB table.

        table_name: string
            Name of the table
        data: dict
            A dictionary of the data you'd like to store in DynamoDB.
        """
        table = self._get_table(table_name)
        return table.put_item(data=data, overwrite=True)

    def delete_items(self, table_name, **kwargs):
        table = self._get_table(table_name)
        res = table.query_2(**kwargs)
        with table.batch_write() as batch:
            for item in res:
                batch.delete_item(**item.get_keys())

    def delete_item(self, table_name, **kwargs):
        """
        Deletes a single item. You can perform a conditional delete operation
        that deletes the item if it exists, or if it has an expected attribute
        value.
        """
        table = self._get_table(table_name)
        table.delete_item(**kwargs)

    def batch_write(self, table_name, data_list):
        table = self._get_table(table_name)
        with table.batch_write() as batch:
            for data in data_list:
                batch.put_item(data=data)

    def get_item(self, table_name, **kwargs):
        """
        Fetches an item (record) from a table in DynamoDB.
        To specify the key of the item you'd like to get, you can specify the
        key attributes as kwargs.

        Returns an ``Item`` instance containing all the data for that record.
        """
        table = self._get_table(table_name)
        return table.get_item(**kwargs)._data

    def get_items(self, table_name, index=None, limit=None, reverse=True,
                  query_filter=None, **kwargs):
        table = self._get_table(table_name)
        res = table.query_2(reverse=reverse, index=index, limit=limit,
                            max_page_size=100, query_filter=query_filter,
                            consistent=True, **kwargs)

        return [i._data for i in res]

    def create_table(self, table_name, schema, indexes=None):
        """
        Creates a new table in DynamoDB & returns an
        in-memory ``Table`` object.
        """
        self._refresh_tables_list()
        if table_name not in self._tables:
            try:
                table = Table.create(table_name, connection=self.conn,
                                     schema=schema, indexes=indexes)
                self._tables[table_name] = table
            except JSONResponseError as ex:
                logging.exception(str(ex))

    def delete_table(self, table_name):
        """
        Deleted existing table
        """
        self._refresh_tables_list()
        if table_name in self._tables:
            try:
                table = self._get_table(table_name)
                table.delete()
            except Exception as ex:
                logging.exception(str(ex))
