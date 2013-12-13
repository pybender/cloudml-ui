
# class TestTasksTests(BaseTestCase):
#     """
#     Tests of the celery tasks.
#     """
#     TEST_NAME = 'Test-1'
#     TEST_NAME2 = 'Test-2'
#     EXAMPLE_NAME = 'Some Example #1-1'
#     MODEL_NAME = 'TrainedModel1'
#     FIXTURES = ('datasets.json', 'models.json', 'tests.json', 'examples.json')

#     @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
#     def test_upload_dataset(self, mock_multipart_upload):
#         from api.tasks import upload_dataset
#         dataset = self.db.DataSet.find_one()
#         upload_dataset(str(dataset._id))
#         mock_multipart_upload.assert_called_once_with(
#             str(dataset._id),
#             dataset.filename,
#             {
#                 'params': str(dataset.import_params),
#                 'handler': dataset.import_handler_id,
#                 'dataset': dataset.name
#             }
#         )
#         dataset.reload()
#         self.assertEquals(dataset.status, dataset.STATUS_IMPORTED)
