from api.amazon_utils import AmazonS3Helper, boto
from moto import mock_s3
from utils import BaseTestCase


class AmazonS3HelperTests(BaseTestCase):
    """
    Tests of AmazonS3Helper class.
    """

    @mock_s3
    def setUp(self):
        super(AmazonS3HelperTests, self).setUp()
        self.helper = AmazonS3Helper(
            token='token', secret='secret', bucket_name='bucket_name'
        )

    @mock_s3
    def test_save_delete_key(self):
        self.helper.save_key_string('some_name', 'test')
        self.helper.delete_key('some_name')
        self.assertIsNone(
            self.helper.conn.get_bucket('bucket_name').get_key('some_name'))
