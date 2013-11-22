import logging

import boto.ec2
from boto.s3.key import Key

from api import app


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
            image_id='ami-14c05a24',#'ami-68c85358',#'ami-a068f590',#'ami-78b42948',#'ami-65821055',#'ami-a7f96b97',#"ami-f0af86b5",#"ami-66c8e123",
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
