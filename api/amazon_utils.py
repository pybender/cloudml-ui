import logging

import boto.ec2
from boto.s3.key import Key

from api import app


class AmazonEC2Helper(object):
    def __init__(self, token=None, secret=None, region='us-west-2'):
        token = token or app.config['AMAZON_ACCESS_TOKEN']
        secret = secret or app.config['AMAZON_TOKEN_SECRET']
        self.conn = boto.ec2.connect_to_region(
            region=region,
            aws_access_key_id=token,
            aws_secret_access_key=secret)

    def terminate_instance(instance_id):
        return self.conn.terminate_instances(
            instance_ids=[instance_id, ])

    def request_spot_instance(instance_type='m3.xlarge'):
        request = conn.request_spot_instances(
            price="1",
            image_id="ami-72f96e42",
            security_group_ids=["sg-1dc1dc71", ],
            instance_type=instance_type,
            placement="us-west-2a",
            subnet_id="subnet-8cf096e5")
        return req[0].instance_id


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

    def save_gz_file(self, key, filename, meta, suffix=''):
        import cStringIO
        import gzip
        key += suffix
        mpu = self.bucket.initiate_multipart_upload(key)
        stream = cStringIO.StringIO()
        compressor = gzip.GzipFile(fileobj=stream, mode='w')

        def uploadPart(partCount=[0]):
            partCount[0] += 1
            stream.seek(0)
            mpu.upload_part_from_file(stream, partCount[0])
            stream.seek(0)
            stream.truncate()

        with file(filename) as inputFile:
            while True:
                chunk = inputFile.read(8192)
                if not chunk:
                    compressor.close()
                    uploadPart()
                    mpu.complete_upload()
                    break
                compressor.write(chunk)
                if stream.tell() > 10 << 20:
                    uploadPart()

    def save_key(self, name, filename, meta={}, compressed=True):
        key = Key(self.bucket)
        key.key = name
        for meta_key, meta_val in meta.iteritems():
            key.set_metadata(meta_key, meta_val)

        headers = {'Content-Type': 'application/octet-stream'}
        if compressed:
            headers['Content-Encoding'] = 'gzip'
        key.set_contents_from_filename(filename, headers)

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