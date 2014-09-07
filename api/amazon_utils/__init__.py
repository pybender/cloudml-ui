import logging
import uuid
from boto.dynamodb2.table import Table

import boto.ec2
from boto.exception import JSONResponseError
from boto.s3.key import Key

from api import app


class AmazonEMRHelper(object):    # pragma: no cover
    def __init__(self, token=None, secret=None, region='us-west-1'):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.conn = boto.emr.connect_to_region(
            region,
            aws_access_key_id=token,
            aws_secret_access_key=secret)

    def terminate_jobflow(self, jobflowid):
        self.conn.terminate_jobflow(jobflowid)

    def describe_jobflow(self, jobflowid):
        return self.conn.describe_jobflow(jobflowid)


class AmazonEC2Helper(object):    # pragma: no cover
    def __init__(self, token=None, secret=None, region='us-west-2'):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.conn = boto.ec2.connect_to_region(
            region,
            aws_access_key_id=token,
            aws_secret_access_key=secret)

    def terminate_instance(self, instance_id):
        return self.conn.terminate_instances(
            instance_ids=[instance_id, ])

    def request_spot_instance(self, instance_type='m3.xlarge'):
        request = self.conn.request_spot_instances(
            price="1",
            image_id='ami-71d49241',#'ami-4e36567e',#'ami-14c05a24',#'ami-68c85358',#'ami-a068f590',#'ami-78b42948',#'ami-65821055',#'ami-a7f96b97',#"ami-f0af86b5",#"ami-66c8e123",
            security_group_ids=["sg-1dc1dc71",],#["sg-534f5d3f", ],
            instance_type=instance_type,
            placement="us-west-2a",
            subnet_id="subnet-7a7c3612")#"subnet-3f5bc256")
        return request[0]

    def get_instance(self, instance_id):
        reservations = self.conn.get_all_instances(instance_ids=[instance_id, ])
        instance = reservations[0].instances[0]
        return instance

    def get_request_spot_instance(self, request_id):
        request = self.conn.get_all_spot_instance_requests(request_ids=[request_id, ])
        request = request[0]
        return request

    def cancel_request_spot_instance(self, request_id):
        request = self.conn.cancel_spot_instance_requests([request_id, ])
        request = request[0]
        return request


class AmazonS3Helper(object):
    def __init__(self, token=None, secret=None, bucket_name=None):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.bucket_name = bucket_name or app.config['AMAZON_BUCKET_NAME']
        self.conn = boto.connect_s3(token, secret)

    @property
    def bucket(self):
        if not hasattr(self, '_bucket'):
            self._bucket = self._get_bucket()
        return self._bucket

    def get_download_url(self, name, expires_in):
        key = Key(self.bucket)
        key.key = name
        return key.generate_url(expires_in)

    def list_keys(self, prefix):
        return self.bucket.list(prefix)

    def load_key(self, name):
        # for i in self.bucket.list():
        #     logging.info(i)
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

    def save_gz_file(self, name, filename, meta={}):  # pragma: no cover
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

        def progress(x,y):
            if y > 0:
                logging.debug("Part %d: %0.2f%%" % (part_count[0], 100.*x/y))

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
                if stream.tell() > 5*1024*1024:
                    upload_part(part_count)

    def save_key(self, name, filename, meta={}, compressed=True):
        key = Key(self.bucket)
        key.key = name
        for meta_key, meta_val in meta.iteritems():
            key.set_metadata(meta_key, meta_val)

        headers = {'Content-Type': 'application/octet-stream'}
        if compressed:
            headers['Content-Encoding'] = 'gzip'
        key.set_contents_from_filename(filename, headers)

    def save_key_string(self, name, data, meta={}):
        key = Key(self.bucket)
        key.key = name
        for meta_key, meta_val in meta.iteritems():
            key.set_metadata(meta_key, meta_val)
        key.set_contents_from_string(data)

    def set_key_metadata(self, name, meta, store_previous=False):
        key = self.bucket.lookup(name)
        for meta_key, meta_val in meta.iteritems():
            if store_previous:
                previous_value = key.get_metadata(meta_key)
                key.set_metadata("previous_" + meta_key, previous_value)
            key.set_metadata(meta_key, meta_val)
        #key.metadata.update(meta)
        #print key, key.metadata
        key.copy(
            key.bucket.name, 
            key.name, 
            key.metadata
        )

    def delete_key(self, name):
        key = Key(self.bucket)
        key.key = name
        key.delete()

    def close(self):
        pass

    def _get_bucket(self):
        #boto.set_stream_logger('boto')
        bucket = self.conn.lookup(self.bucket_name)
        if bucket is None:
            bucket = self.conn.create_bucket(self.bucket_name)
        return bucket


class AmazonDynamoDBHelper(object):
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
        self._queries = {}

    @property
    def conn(self):
        if not self._conn:
            from boto import dynamodb2
            from boto.dynamodb2.layer1 import DynamoDBConnection

            if app.config.get('TEST_MODE'):
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
        if not table_name in self._tables:
            self._refresh_tables_list()

        return self._tables[table_name]

    def _refresh_tables_list(self):
        from boto.dynamodb2.table import Table
        self._tables = {}
        for table_name in self.conn.list_tables()['TableNames']:
            self._tables[table_name] = Table(table_name,
                                             connection=self.conn)

    def put_item(self, table_name, data):
        table = self._get_table(table_name)
        return table.put_item(data=data, overwrite=True)

    def delete_items(self, table_name, **kwargs):
        table = self._get_table(table_name)
        res = table.query(**kwargs)
        with table.batch_write() as batch:
            for item in res:
                batch.delete_item(**item.get_keys())

    def batch_write(self, table_name, data_list):
        table = self._get_table(table_name)
        with table.batch_write() as batch:
            for data in data_list:
                batch.put_item(data=data)

    def get_item(self, table_name, **kwargs):
        table = self._get_table(table_name)
        return table.get_item(**kwargs)._data

    def get_items(self, table_name, limit=None, reverse=True,
                  next_token=None, **kwargs):
        table = self._get_table(table_name)
        next_token = next_token or None
        res = self._queries.get(next_token) if next_token else None

        if not res:
            # This is a hack for
            # "There are too many conditions in this query" issue
            if len(kwargs.keys()) > 2:
                # Slow!
                res = table.scan(
                    max_page_size=limit,
                    **kwargs
                )
            else:
                res = table.query(
                    max_page_size=limit,
                    reverse=reverse,
                    **kwargs
                )
            next_token = str(uuid.uuid1())
            self._queries[next_token] = res

        items = []
        if limit:
            for i in range(limit):
                try:
                    item = next(res)
                except StopIteration:
                    next_token = None
                    break
                items.append(item._data)
        else:
            items = [item._data for item in res]

        return items, next_token

    def create_table(self, table_name, schema):
        self._refresh_tables_list()
        if not table_name in self._tables:
            try:
                Table.create(table_name, connection=self.conn, schema=schema)
                self._tables[table_name] = Table(table_name,
                                                 connection=self.conn)
            except JSONResponseError as ex:
                logging.exception(str(ex))
