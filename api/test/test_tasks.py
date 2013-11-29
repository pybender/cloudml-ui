# -*- coding: utf8 -*-

from api.tasks import InvalidOperationError
import os
import json
from bson import ObjectId

from moto import mock_s3
from mock import patch, MagicMock, Mock

from api import app
from constants import DATASET_ID, TEST1_ID, TEST2_ID, QUEUED_TEST4_ID
from utils import BaseTestCase


class TestTasksTests(BaseTestCase):
    """
    Tests of the celery tasks.
    """
    TEST_NAME = 'Test-1'
    TEST_NAME2 = 'Test-2'
    EXAMPLE_NAME = 'Some Example #1-1'
    MODEL_NAME = 'TrainedModel1'
    FIXTURES = ('datasets.json', 'models.json', 'tests.json', 'examples.json')

    def setUp(self):
        super(TestTasksTests, self).setUp()
        self.test = self.db.Test.find_one({'_id': ObjectId(TEST1_ID)})
        self.test2 = self.db.Test.find_one({'_id': ObjectId(TEST2_ID)})
        self.dataset = self.db.DataSet.find_one({'_id': ObjectId(DATASET_ID)})
        self.examples_count = self.db.TestExample.find(
            {'test_name': self.TEST_NAME}).count()
        self.real_chunks_config = app.config['EXAMPLES_CHUNK_SIZE']
        app.config['EXAMPLES_CHUNK_SIZE'] = 10

    def tearDown(self):
        super(TestTasksTests, self).tearDown()
        app.config['EXAMPLES_CHUNK_SIZE'] = self.real_chunks_config

    def _set_probabilities(self, probabilities):
        for example in self.db.TestExample.find({'test_name': self.TEST_NAME}):
            label, prob = probabilities[example['id']]
            example['test_id'] = str(self.test._id)
            example['label'] = label
            example['prob'] = prob
            example.save()

    def test_calculate_confusion_matrix(self):
        from api.tasks import calculate_confusion_matrix

        def _assertMatrix(w0, w1, expected):
            result = calculate_confusion_matrix(self.test._id, w0, w1)
            self.assertEquals(result, expected)
            self.assertEquals(self.examples_count, sum([sum(row) for row in result]))

        self._set_probabilities({
            '1':  ('0', [0.3, 0.7]),
            '1a': ('0', [0.9, 0.1]),
            '2':  ('1', [0.3, 0.7]),
            '4':  ('1', [0.2, 0.8]),
        })

        _assertMatrix(1, 1, [[1, 1], [0, 2]])
        _assertMatrix(0.5, 0.5, [[1, 1], [0, 2]])

        _assertMatrix(1, 10, [[0, 2], [0, 2]])
        _assertMatrix(1, 100, [[0, 2], [0, 2]])
        _assertMatrix(10, 1, [[2, 0], [2, 0]])
        _assertMatrix(100, 1, [[2, 0], [2, 0]])
        _assertMatrix(0, 1, [[0, 2], [0, 2]])
        _assertMatrix(1, 0, [[2, 0], [2, 0]])
        _assertMatrix(1, 3, [[1, 1], [0, 2]])
        _assertMatrix(3, 1, [[2, 0], [1, 1]])

        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 0, 0)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, -1, 1)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 1, -1)
        self.assertRaises(ValueError, calculate_confusion_matrix, ObjectId(), 1, 1)

        self.test.model_id = str(ObjectId())
        self.test.save()
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 2, 1)

    @mock_s3
    @patch('api.models.DataSet.get_data_stream')
    def test_get_csv_results(self, mock_get_data_stream):
        from api.tasks import get_csv_results

        fields = ['label', 'pred_label', 'prob']
        url = get_csv_results(self.test.model_id, self.test._id, fields)

        test = self.db.Test.find_one({'name': self.TEST_NAME})

        self.assertTrue(url)
        self.assertEquals(test.exports[0]['url'], url)
        self.assertEquals(test.exports[0]['fields'], fields)
        # Data wasn't loaded from s3:
        self.assertFalse(mock_get_data_stream.called)

        url = get_csv_results(self.test.model_id, self.test2._id, fields)

        test = self.db.Test.find_one({'name': self.TEST_NAME2})

        self.assertTrue(url)
        self.assertEquals(test.exports[0]['url'], url)
        self.assertEquals(test.exports[0]['fields'], fields)
        # Data was loaded from s3:
        self.assertTrue(mock_get_data_stream.called)

    @mock_s3
    @patch('api.models.Model.get_trainer')
    @patch('api.models.DataSet.get_data_stream')
    @patch('api.tasks.store_examples')
    def _check_run_test(self, test, _fake_raw_data=None, *mocks):
        mock_store_examples, mock_get_data_stream, mock_get_trainer = mocks
        import numpy
        import scipy
        from api.tasks import run_test

        if _fake_raw_data is None:
            _fake_raw_data = [{'application_id': '123',
                               'hire_outcome': '0',
                               'title': 'A1'}] * 100

        def _fake_test(self, *args, **kwargs):
            _fake_test.called = True
            self._raw_data = _fake_raw_data
            metrics_mock = MetricsMock()
            preds = Mock()
            preds.size = 100
            preds.__iter__ = Mock(return_value=iter([0] * 100))
            metrics_mock._preds = preds

            metrics_mock._probs = [numpy.array([0.1, 0.2])] * 100

            metrics_mock._true_data = scipy.sparse.coo_matrix([[0, 0, 0]] * 100)

            return metrics_mock

        mock_apply_async = MagicMock()
        mock_store_examples.si.return_value = mock_apply_async
        mocks = list(mocks)
        mocks.append(mock_apply_async)

        # Set up mock trainer
        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(
            open('./api/fixtures/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        with patch('core.trainer.trainer.Trainer.test',
                   _fake_test) as mock_test:
            mocks.append(mock_test)
            return run_test([self.dataset._id, ], test._id), mocks

    def test_run_test_with_untrained_model(self):
        from api.tasks import run_test
        test = app.db.Test.get_from_id(ObjectId(QUEUED_TEST4_ID))
        model = test.model
        model.status = model.STATUS_NEW
        model.save()
        self.assertRaises(InvalidOperationError, run_test,
                          [self.dataset._id, ], self.test._id)

    def test_run_test_unicode_encoding(self):
         # Unicode encoding test
        test = app.db.Test.get_from_id(ObjectId(QUEUED_TEST4_ID))
        unicode_string = u'Привет!'
        _fake_raw_data = [{'application_id': '123',
                           'hire_outcome': '0',
                           'title': 'A1',
                           'opening_title': unicode_string,
                           'opening_id': unicode_string}] * 100
        
        result, mocks = self._check_run_test(test, _fake_raw_data)
        self.assertEquals(result, 'Test completed')
        example = self.db.TestExample.find_one(
            {'test_id': str(test._id)})
        self.assertEquals(example.id, unicode_string)
        self.assertEquals(example.name, unicode_string)

    def test_run_test_examples_to_amazon(self):
        test = app.db.Test.get_from_id(ObjectId(QUEUED_TEST4_ID))
        test.status = test.STATUS_QUEUED
        test.examples_placement = test.EXAMPLES_TO_AMAZON_S3
        test.examples_fields = ["hire_outcome", "application_id"]
        test.save()

        result, mocks = self._check_run_test(test, None)
        mock_store_examples, mock_get_data_stream, mock_get_trainer, \
            mock_apply_async, mock_test = mocks
        self.assertTrue(mock_test.called)
        self.assertEquals(result, 'Test completed')

        test = app.db.Test.find_one({'_id': test._id})
        self.assertEquals(test.status, test.STATUS_COMPLETED)
        self.assertEquals(test.classes_set, MetricsMock.classes_set)
        self.assertEquals(test.accuracy, MetricsMock.accuracy)
        self.assertTrue(test.memory_usage['testing'],
                        "Memory usage for testing was not filled")
        self.assertEquals(test.dataset._id, self.dataset._id)

        examples_count = app.db.TestExample.find({'test_name': test.name}).count()
        self.assertTrue(examples_count == test.examples_count == 100)
        example = app.db.TestExample.find_one({'test_id': str(test._id)})

        # TODO: Check whether all data saved to amazon s3
        self.assertEquals(10, mock_store_examples.si.call_count)
        self.assertEquals(10, mock_apply_async.apply.call_count)

        self.assertTrue(example.data_input, 'Raw data should be filled to MongoDB')
        self.assertEquals(example.data_input.keys(), test.examples_fields)

        test = self.db.Test.get_from_id(ObjectId(self.test._id))

        app.config['EXAMPLES_CHUNK_SIZE'] = 5
        result, mocks = self._check_run_test(test, None)
        mock_store_examples, mock_get_data_stream, mock_get_trainer, \
            mock_apply_async, mock_test = mocks

        self.assertEquals(result, 'Test completed')
        self.assertEquals(5, mock_store_examples.si.call_count)
        self.assertEquals(5, mock_apply_async.apply.call_count)

        app.config['EXAMPLES_CHUNK_SIZE'] = 7
        result, mocks = self._check_run_test(test, None)
        mock_store_examples, mock_get_data_stream, mock_get_trainer, \
            mock_apply_async, mock_test = mocks
        self.assertEquals(result, 'Test completed')
        self.assertEquals(7, mock_store_examples.si.call_count)
        self.assertEquals(7, mock_apply_async.apply.call_count)
        mock_store_examples.reset_mock()
        mock_apply_async.reset_mock()

    def test_run_test_examples_to_mongo(self):
        test = app.db.Test.get_from_id(ObjectId(QUEUED_TEST4_ID))
        test.status = test.STATUS_QUEUED
        test.examples_placement = test.EXAMPLES_MONGODB
        test.examples_fields = ["hire_outcome", "application_id"]
        test.save()

        self.assertEquals(
            app.db.TestExample.find({'test_id': str(test._id)}).count(), 0)

        result, mocks = self._check_run_test(test, None)
        self.assertEquals(result, 'Test completed')

        mock_store_examples, mock_get_data_stream, mock_get_trainer, \
            mock_apply_async, mock_run_test = mocks
        self.assertEquals(1, mock_get_data_stream.call_count,
                          'Should be cached and called only once')
        self.assertFalse(
            mock_store_examples.si.call_count,
            "Examples placement is MongoDB. We do not need to store it in Amazon S3")
        self.assertFalse(mock_apply_async.apply.call_count)

        example = app.db.TestExample.find_one({'test_id': str(test._id)})
        self.assertTrue(example.data_input, 'Raw data should be filled at all')
        self.assertEquals(example.data_input.keys(), ['hire_outcome', 'application_id'])

    def test_run_test_dont_save_examples(self):
        test = app.db.Test.get_from_id(ObjectId(QUEUED_TEST4_ID))
        test.status = test.STATUS_QUEUED
        test.examples_placement = test.EXAMPLES_DONT_SAVE
        test.examples_fields = ["hire_outcome", "application_id"]
        test.save()

        test_examples = app.db.TestExample.find({'test_id': str(test._id)})
        self.assertEquals(test_examples.count(), 0)

        result, mocks = self._check_run_test(test, None)
        self.assertEquals(result, 'Test completed')

        mock_store_examples, mock_get_data_stream, mock_get_trainer, \
            mock_apply_async, mock_run_test = mocks
        self.assertEquals(1, mock_get_data_stream.call_count,
                          'Should be cached and called only once')
        self.assertFalse(
            mock_store_examples.si.call_count,
            "We do not need to store examples to Amazon S3")
        self.assertFalse(mock_apply_async.apply.call_count)
        example = app.db.TestExample.find_one({'test_id': str(test._id)})
        self.assertFalse(example.data_input,
                         'Raw data should not be filled at all')

    @mock_s3
    def test_store_examples(self):
        from api.tasks import store_examples

        _ROW_COUNT = 5

        filename = 'Test_raw_data-{0!s}.dat'.format(str(self.test._id))
        with open(os.path.join(app.config['DATA_FOLDER'], filename), 'w') as fp:
            fp.writelines(['{"data": "value"}\n'] * _ROW_COUNT)

        example = self.db.TestExample.find_one({'name': self.EXAMPLE_NAME})
        example.on_s3 = True
        example.save()

        result = store_examples(self.test._id, [
            range(_ROW_COUNT), [str(example._id)] * _ROW_COUNT
        ])
        self.assertEquals(result, list(zip(
            range(_ROW_COUNT), [str(example._id)] * _ROW_COUNT)))

        example.reload()
        self.assertEquals(example.data_input, {})
        self.assertEquals(json.loads(example._load_from_s3()), {'data': 'value'})

    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    def test_upload_dataset(self, mock_multipart_upload):
        from api.tasks import upload_dataset
        dataset = self.db.DataSet.find_one()
        upload_dataset(str(dataset._id))
        mock_multipart_upload.assert_called_once_with(
            str(dataset._id),
            dataset.filename,
            {
                'params': str(dataset.import_params),
                'handler': dataset.import_handler_id,
                'dataset': dataset.name
            }
        )
        dataset.reload()
        self.assertEquals(dataset.status, dataset.STATUS_IMPORTED)


class MetricsMock(MagicMock):
    accuracy = 0.85
    classes_set = ['0', '1']
    _labels = ['0', '1'] * 50

    def get_metrics_dict(self):
        return {
            'confusion_matrix': [0, 0],
            'roc_curve': [[0], [0], [0], [0]],
            'precision_recall_curve': [[0], [0], [0], [0]],
        }
