"""
Unittests of the Amazon services helper classes.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from cloudml.tests.test_utils import StreamPill
import boto3
import os
from mock import patch, ANY
from botocore.exceptions import ClientError, ParamValidationError
from botocore.response import StreamingBody
from boto3.dynamodb.conditions import Key
from flask.ext.testing import TestCase
from api.amazon_utils import AmazonS3Helper, AmazonDynamoDBHelper, \
    AmazonS3ObjectNotFound, AmazonEMRHelper, AmazonEC2Helper, S3ResponseError
from api import app


class AmazonS3HelperTests(TestCase):
    """ Tests of AmazonS3Helper class. """

    PILL_RESPONSES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'pill/s3/'))

    def setUp(self):
        super(AmazonS3HelperTests, self).setUp()
        self.pill = StreamPill(debug=False)
        self.session = boto3.session.Session()
        boto3.DEFAULT_SESSION = self.session
        self.credentials = {'token': 'token', 'secret': 'secret',
                            'bucket_name': 'bucket_name'}

    def test_get_dnowload_url(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'download_url'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        self.assertTrue(helper.get_download_url('test', 3600))
        self.assertRaises(ValueError, helper.get_download_url, 'test', 'time')

    def test_list_keys(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'list_keys'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        # ListObjects_1
        res = helper.list_keys('prefix')
        self.assertEqual(set(['a', 'b', 'c']), set([k['Key'] for k in res]))
        # ListObjects_2
        self.assertEqual([], helper.list_keys('another_prefix'))
        self.assertRaises(ParamValidationError, helper.list_keys, None)

    def test_load_key(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'load_key'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        # GetObject_1
        res = helper.load_key('name')
        self.assertTrue(isinstance(res, basestring))

        # GetObject_2
        res = helper.load_key('name', with_metadata=True)
        self.assertTrue(isinstance(res, dict))
        self.assertTrue(isinstance(res['Body'], StreamingBody))
        self.assertEqual(res['Metadata']['Name'], 'name')

        # GetObject_3-6
        self.assertRaises(AmazonS3ObjectNotFound, helper.load_key, 'any')

    def test_put_file(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'put'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        with patch("boto3.s3.transfer.S3Transfer._multipart_upload") as mu:
            app.config['MULTIPART_UPLOAD_CHUNK_SIZE'] = 128
            helper.save_gz_file('name',
                                os.path.join(self.PILL_RESPONSES_DIR,
                                             'put/test_file.py'),
                                {'model_id': 234})
            mu.assert_called_with(os.path.join(self.PILL_RESPONSES_DIR,
                                               'put/test_file.py'),
                                  'bucket_name', 'name', ANY, ANY)

        # PutObject_1
        self.assertTrue(helper.save_key('name',
                                        os.path.join(self.PILL_RESPONSES_DIR,
                                                     'put/test_file.py'),
                                        {'model_id': 234}, compressed=False))
        # PutObject_2
        self.assertTrue(helper.save_key('name',
                                        os.path.join(self.PILL_RESPONSES_DIR,
                                                     'put/test_file.py'),
                                        {'model_id': 234}))
        # PutObject_3
        self.assertTrue(helper.save_key_string('name', 'data',
                                               {'model_id': 234}))

    def test_set_key_metadata(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'metadata'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        # Key not found (HeadObject_1)
        self.assertRaises(AmazonS3ObjectNotFound, helper.set_key_metadata,
                          'name', {})
        # Key exists, empty metadata
        self.assertTrue(helper.set_key_metadata('name',
                                                meta={'Name': 'new_name',
                                                      'Other': 'value',
                                                      'Third': '3value'},
                                                store_previous=True))

    def test_delete_key(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'delete_key'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        self.assertTrue(helper.delete_key('name'))

    def test_key_exists(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'key_exists'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        # HeadObject_1
        self.assertFalse(helper.key_exists('name'))
        # HeadObject_2
        self.assertTrue(helper.key_exists('name'))

    def test_check_or_create_bucket(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'bucket'))
        self.pill.playback()

        helper = AmazonS3Helper(**self.credentials)
        # HeadBucket_1
        self.assertRaises(S3ResponseError, helper._check_or_create_bucket)

        # HeadBucket_2
        self.assertTrue(helper._check_or_create_bucket())

        # HeadBucket_3
        self.assertTrue(helper._check_or_create_bucket())

    def create_app(self):
        return app


class AmazonDynamoDBHelperTests(TestCase):
    """
    You need local dynamodb to be running for these tests
    see api/logs/dynamodb/dynamodb_local.sh to be
    """
    TEST_TABLE_NAME = 'test_table'
    PILL_RESPONSES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'pill/dynamodb/'))

    def setUp(self):
        super(AmazonDynamoDBHelperTests, self).setUp()
        self.pill = StreamPill(debug=False)
        self.session = boto3.session.Session()
        boto3.DEFAULT_SESSION = self.session

    def test_create_table(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'create_table'))
        self.pill.playback()
        SCHEMA = [{'AttributeName': 'object_id', 'KeyType': 'HASH'},
                  {'AttributeName': 'id', 'KeyType': 'RANGE'}]

        SCHEMA_TYPES = [{'AttributeName': 'object_id', 'AttributeType': 'N'},
                        {'AttributeName': 'id', 'AttributeType': 'S'}]

        helper = AmazonDynamoDBHelper()
        self.assertFalse(self.TEST_TABLE_NAME in helper._tables)
        helper.create_table(self.TEST_TABLE_NAME, SCHEMA, SCHEMA_TYPES)
        self.assertTrue(self.TEST_TABLE_NAME in helper._tables)
        self.assertTrue(helper._get_table(self.TEST_TABLE_NAME))

    def test_put_get_delete(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'put_get_del'))
        self.pill.playback()
        helper = AmazonDynamoDBHelper()
        # put
        self.assertTrue(helper.put_item(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            {'object_id': 1, 'id': 'one', 'data': 'd1'}))

        # should work without exceptions
        helper.batch_write(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            [{'object_id': 2, 'id': 'two', 'data': 'd1'},
             {'object_id': 3, 'id': 'three', 'data': 'd3'}])

        # get
        item = helper.get_item(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME, object_id=1)
        self.assertEqual(item['object_id'], 1)

        items = helper.get_items(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            KeyConditionExpression=Key('object_id').eq(1) & Key('id').eq('one')
        )
        self.assertTrue(isinstance(items, list))
        self.assertEqual(items[0]['object_id'], 1)

        # delete
        self.assertTrue(helper.delete_item(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            object_id=1))
        # should work without exceptions
        helper.delete_items(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME, ['object_id', 'id'],
            KeyConditionExpression=Key('object_id').eq(2))

    def create_app(self):
        return app


class AmazonEMRHelperTests(TestCase):
    """ Tests of AmazonEMRHelper class. """

    PILL_RESPONSES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'pill/emr/'))

    def setUp(self):
        super(AmazonEMRHelperTests, self).setUp()
        self.pill = StreamPill(debug=False)
        self.session = boto3.session.Session()
        boto3.DEFAULT_SESSION = self.session
        self.credentials = {'token': 'token', 'secret': 'secret',
                            'region': 'region'}

    def create_app(self):
        return app

    def test_terminate_jobflow(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'terminate'))
        self.pill.playback()

        helper = AmazonEMRHelper(**self.credentials)
        self.assertFalse(helper.terminate_jobflow('job_flow_id'))

    def test_describe_jobflow(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'describe'))
        self.pill.playback()

        helper = AmazonEMRHelper(**self.credentials)
        result = helper.describe_jobflow('job_flow_id')
        self.assertTrue(isinstance(result, dict))
        self.assertTrue('ExecutionStatusDetail' in result)
        self.assertTrue('State' in result['ExecutionStatusDetail'])


class AmazonEC2HelperTests(TestCase):
    """ Tests of AmazonEC2Helper class. """

    PILL_RESPONSES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'pill/ec2/'))

    def setUp(self):
        super(AmazonEC2HelperTests, self).setUp()
        self.pill = StreamPill(debug=False)
        self.session = boto3.session.Session()
        boto3.DEFAULT_SESSION = self.session
        self.credentials = {'token': 'token', 'secret': 'secret',
                            'region': 'region'}

    def create_app(self):
        return app

    def test_terminate_instance(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'terminate'))
        self.pill.playback()

        helper = AmazonEC2Helper(**self.credentials)
        self.assertTrue(helper.terminate_instance('instance_id'))

    def test_request_spot_instance(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'request_spot'))
        self.pill.playback()

        helper = AmazonEC2Helper(**self.credentials)
        result = helper.request_spot_instance()
        self.assertTrue(result)
        self.assertTrue('SpotInstanceRequestId' in result)

    def test_get_instance(self):
        import logging
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'get_instance'))
        self.pill.playback()

        helper = AmazonEC2Helper(**self.credentials)
        self.assertTrue(helper.get_instance('instance_id'))

    def test_get_request_spot_instance(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'get_request'))
        self.pill.playback()

        helper = AmazonEC2Helper(**self.credentials)
        result = helper.get_request_spot_instance('request_id')
        self.assertTrue(result)
        self.assertTrue('SpotInstanceRequestId' in result)

    def test_cancel_request_spot_instance(self):
        # Amazon mock
        self.pill.attach(self.session,
                         os.path.join(self.PILL_RESPONSES_DIR, 'cancel'))
        self.pill.playback()

        helper = AmazonEC2Helper(**self.credentials)
        result = helper.cancel_request_spot_instance('request_id')
        self.assertTrue(result)
        self.assertTrue('SpotInstanceRequestId' in result)
