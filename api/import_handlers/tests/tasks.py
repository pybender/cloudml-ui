from mock import patch

from api.base.test_utils import BaseDbTestCase
from ..fixtures import DataSetData
from ..models import DataSet, db
from ..tasks import upload_dataset, _get_uncompressed_filesize


class TestTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [DataSetData]

    @patch('api.logs.models.LogMessage')
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_upload_dataset(self, mock_multipart_upload, *mocks):
        dataset = DataSet.query.first()
        upload_dataset(dataset.id)
        mock_multipart_upload.assert_called_once_with(
            dataset.uid,
            dataset.filename,
            {
                'params': str(dataset.import_params),
                'handler': dataset.import_handler_id,
                'dataset': dataset.name
            }
        )
        db.session.expire(dataset)
        self.assertEquals(dataset.status, dataset.STATUS_IMPORTED)

    def test_get_uncompressed_filesize(self):
        self.assertEquals(
            258447,
            _get_uncompressed_filesize('api/import_handlers/fixtures/ds.gz'))

        # a speical test for crossing 2GB limit
        # self.assertEquals(
        #    2447003648,
        #    _get_uncompressed_filesize('/home/nader/host-share/toolarge.gz'))
