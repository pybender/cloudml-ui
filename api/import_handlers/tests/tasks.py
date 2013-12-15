from mock import patch

from api.base.test_utils import BaseDbTestCase
from ..fixtures import DataSetData
from ..models import DataSet, db
from ..tasks import upload_dataset


class TestTasksTests(BaseDbTestCase):
    """ Tests of the celery tasks. """
    datasets = [DataSetData]

    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_upload_dataset(self, mock_multipart_upload):
        dataset = DataSet.query.first()
        upload_dataset(dataset.id)
        mock_multipart_upload.assert_called_once_with(
            dataset.id,
            dataset.filename,
            {
                'params': str(dataset.import_params),
                'handler': dataset.import_handler_id,
                'dataset': dataset.name
            }
        )
        db.session.expire(dataset)
        self.assertEquals(dataset.status, dataset.STATUS_IMPORTED)
