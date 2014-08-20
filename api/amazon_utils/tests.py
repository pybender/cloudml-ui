#from mock import patch
from boto.dynamodb2.types import NUMBER, STRING
from moto import mock_s3, mock_dynamodb2
from flask.ext.testing import TestCase
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.fields import RangeKey

from api.amazon_utils import AmazonS3Helper, AmazonDynamoDBHelper
from api import app


class AmazonS3HelperTests(TestCase):
    """ Tests of AmazonS3Helper class. """

    @mock_s3
    def setUp(self):
        super(AmazonS3HelperTests, self).setUp()
        self.helper = AmazonS3Helper(
            token='token', secret='secret', bucket_name='bucket_name'
        )

    def create_app(self):
        return app

    @mock_s3
    def test_save_delete_key(self):
        self.helper.save_key_string('some_name', 'test')
        self.helper.delete_key('some_name')
        self.assertIsNone(
            self.helper.bucket.get_key('some_name'))


class AmazonDynamoDBHelperTests(TestCase):
    """
    You need local dynamodb to be running for these tests
    see api/logs/dynamodb/dynamodb_local.sh to be
    """
    TEST_TABLE_NAME = 'test_table'

    def setUp(self):
        super(AmazonDynamoDBHelperTests, self).setUp()
        self.helper = AmazonDynamoDBHelper()
        self.dynamodb_mock = mock_dynamodb2()
        self.dynamodb_mock.start()

        self.helper.create_table(AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
                                 [HashKey('object_id', data_type=NUMBER),
                                  RangeKey('id', data_type=STRING)])

    def tearDown(self):
        super(AmazonDynamoDBHelperTests, self).tearDown()
        self.dynamodb_mock.stop()

    def create_app(self):
        return app

    def test_create_table(self):
        self.assertIsNotNone(
            self.helper._get_table(AmazonDynamoDBHelperTests.TEST_TABLE_NAME))
        # shouldn't cause any problems
        self.helper.create_table(AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
                                 [HashKey('object_id', data_type=NUMBER),
                                  RangeKey('id', data_type=STRING)])

    def test_put_get_item(self):
        self.helper.put_item(AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
                             {'object_id': 1, 'id': 'one', 'data': 'd1'})
        self.helper.put_item(AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
                             {'object_id': 2, 'id': 'two', 'data': 'd2'})
        self.helper.put_item(AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
                             {'object_id': 3, 'id': 'three', 'data': 'd3'})

        self.assertEqual(self.helper.get_item(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME, object_id=1, id='one'),
            {'object_id': 1, 'id': 'one', 'data': 'd1'})
        self.assertEqual(self.helper.get_item(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME, object_id=2, id='two'),
            {'object_id': 2, 'id': 'two', 'data': 'd2'})

    def test_batch_write_get_items_delete_items(self):
        self.helper.batch_write(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            [{'object_id': 1, 'id': 'one', 'data': 'd1'},
             {'object_id': 2, 'id': 'two', 'data': 'd2'},
             {'object_id': 3, 'id': 'three', 'data': 'd3'}])
        items, _ = self.helper.get_items(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            object_id__eq=3, id__eq='three')
        self.assertEqual(
            items, [{'object_id': 3, 'id': 'three', 'data': 'd3'}])

        self.helper.delete_items(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            object_id__eq=2, id__eq='two')

        items, _ = self.helper.get_items(
            AmazonDynamoDBHelperTests.TEST_TABLE_NAME,
            object_id__eq=2, id__eq='two')
        self.assertEqual(items, [])
