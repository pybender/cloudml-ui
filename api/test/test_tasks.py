from bson import ObjectId

from moto import mock_s3
from mock import patch, MagicMock, Mock

from api import app
from utils import BaseTestCase


class TestTasksTests(BaseTestCase):
    """
    Tests of the celery tasks.
    """
    TEST_NAME = 'Test-1'
    DS_ID = '5270dd3a106a6c1631000000'
    FIXTURES = ('datasets.json', 'models.json', 'tests.json', 'examples.json')

    def setUp(self):
        super(TestTasksTests, self).setUp()
        self.test = self.db.Test.find_one({'name': self.TEST_NAME})
        self.dataset = self.db.DataSet.find_one({'_id': ObjectId(self.DS_ID)})
        self.examples_count = self.db.TestExample.find(
            {'test_name': self.TEST_NAME}).count()
        self.real_chunks_config = app.config['EXAMPLES_CHUNK_SIZE']
        app.config['EXAMPLES_CHUNK_SIZE'] = 10
        self.real_size_config = app.config['MAX_MONGO_EXAMPLE_SIZE']
        app.config['MAX_MONGO_EXAMPLE_SIZE'] = 10

    def tearDown(self):
        super(TestTasksTests, self).tearDown()
        app.config['EXAMPLES_CHUNK_SIZE'] = self.real_chunks_config
        app.config['MAX_MONGO_EXAMPLE_SIZE'] = self.real_size_config

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
        self.assertTrue(mock_get_data_stream.called)

    @mock_s3
    @patch('api.models.DataSet.get_data_stream')
    @patch('api.tasks.store_examples')
    def test_run_test(self, mock_store_examples, mock_get_data_stream):
        from api.tasks import run_test

        def _fake_test(self, *args, **kwargs):
            class MetricsMock(MagicMock):
                accuracy = 1.0
                classes_set = ['0', '1']
                _labels = ['0', '1'] * 50

                def get_metrics_dict(self):
                    return {
                        'confusion_matrix': [0, 0],
                        'roc_curve': [[0], [0], [0], [0]],
                        'precision_recall_curve': [[0], [0], [0], [0]],
                    }

            _fake_test.called = True

            self._raw_data = [{'data': 'some-data-here'}] * 100

            metrics_mock = MetricsMock()
            preds = Mock()
            preds.size = 100
            preds.__iter__ = Mock(return_value=iter([0] * 100))
            metrics_mock._preds = preds

            m = MagicMock(side_effect=[MagicMock()] * 100)

            metrics_mock._probs = MagicMock()
            metrics_mock._probs.__iter__ = Mock(return_value=iter([m] * 100))

            metrics_mock._true_data = MagicMock()
            todense = MagicMock()
            todense.__iter__ = Mock(return_value=iter([m] * 100))
            metrics_mock._true_data.todense.return_value = todense

            return metrics_mock

        mock_apply_async = MagicMock()
        mock_store_examples.si.return_value = mock_apply_async

        with patch('core.trainer.trainer.Trainer.test',
                   _fake_test) as mock_test:

            result = run_test(self.dataset._id, self.test._id)
            self.assertTrue(mock_test.called)

            self.assertEquals(result, 'Test completed')

            # Should be cached and called only once
            self.assertEquals(1, mock_get_data_stream.call_count)

            self.assertEquals(10, mock_store_examples.si.call_count)
            self.assertEquals(10, mock_apply_async.apply.call_count)

            mock_store_examples.reset_mock()
            mock_apply_async.reset_mock()

            app.config['EXAMPLES_CHUNK_SIZE'] = 5

            result = run_test(self.dataset._id, self.test._id)
            self.assertEquals(result, 'Test completed')
            self.assertEquals(5, mock_store_examples.si.call_count)
            self.assertEquals(5, mock_apply_async.apply.call_count)

            mock_store_examples.reset_mock()
            mock_apply_async.reset_mock()

            app.config['EXAMPLES_CHUNK_SIZE'] = 7

            result = run_test(self.dataset._id, self.test._id)
            self.assertEquals(result, 'Test completed')
            self.assertEquals(7, mock_store_examples.si.call_count)
            self.assertEquals(7, mock_apply_async.apply.call_count)

            mock_store_examples.reset_mock()
            mock_apply_async.reset_mock()

            app.config['MAX_MONGO_EXAMPLE_SIZE'] = 5000

            result = run_test(self.dataset._id, self.test._id)
            self.assertEquals(result, 'Test completed')
            self.assertFalse(mock_store_examples.si.called)
            self.assertFalse(mock_apply_async.apply.called)
