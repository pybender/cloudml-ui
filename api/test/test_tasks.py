# -*- coding: utf8 -*-

from api.tasks import InvalidOperationError
import os
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
    TEST_NAME2 = 'Test-2'
    DS_ID = '5270dd3a106a6c1631000000'
    EXAMPLE_NAME = 'Some Example #1-1'
    MODEL_NAME = 'TrainedModel1'
    FIXTURES = ('datasets.json', 'models.json', 'tests.json', 'examples.json')

    def setUp(self):
        super(TestTasksTests, self).setUp()
        self.test = self.db.Test.find_one({'name': self.TEST_NAME})
        self.test2 = self.db.Test.find_one({'name': self.TEST_NAME2})
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
    def test_run_test(self, mock_store_examples, mock_get_data_stream,
                      mock_get_trainer):
        import numpy
        import scipy
        from api.tasks import run_test

        _fake_raw_data = [{'data': 'some-data-here'}] * 100

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

        # Set up mock trainer
        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(
            open('./api/fixtures/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        model = self.db.Model.find_one()

        self.test.model_id = str(model._id)
        self.test.model = model
        self.test.save()

        self.test2.model_id = str(model._id)
        self.test2.model = model
        self.test2.save()

        with patch('core.trainer.trainer.Trainer.test',
                   _fake_test) as mock_test:

            result = run_test([self.dataset._id, ], self.test._id)
            self.assertTrue(mock_test.called)

            self.assertEquals(result, 'Test completed')

            # Should be cached and called only once
            self.assertEquals(1, mock_get_data_stream.call_count)

            self.assertEquals(10, mock_store_examples.si.call_count)
            self.assertEquals(10, mock_apply_async.apply.call_count)

            test = self.db.Test.get_from_id(ObjectId(self.test._id))
            self.assertEquals(test.dataset._id, self.dataset._id)

            mock_store_examples.reset_mock()
            mock_apply_async.reset_mock()

            app.config['EXAMPLES_CHUNK_SIZE'] = 5

            result = run_test([self.dataset._id, ], self.test._id)
            self.assertEquals(result, 'Test completed')
            self.assertEquals(5, mock_store_examples.si.call_count)
            self.assertEquals(5, mock_apply_async.apply.call_count)

            mock_store_examples.reset_mock()
            mock_apply_async.reset_mock()

            app.config['EXAMPLES_CHUNK_SIZE'] = 7

            result = run_test([self.dataset._id, ], self.test._id)
            self.assertEquals(result, 'Test completed')
            self.assertEquals(7, mock_store_examples.si.call_count)
            self.assertEquals(7, mock_apply_async.apply.call_count)

            mock_store_examples.reset_mock()
            mock_apply_async.reset_mock()

            app.config['MAX_MONGO_EXAMPLE_SIZE'] = 5000

            result = run_test([self.dataset._id, ], self.test._id)
            self.assertEquals(result, 'Test completed')
            self.assertFalse(mock_store_examples.si.called)
            self.assertFalse(mock_apply_async.apply.called)

            model.status = model.STATUS_NEW
            model.save()
            self.assertRaises(InvalidOperationError, run_test,
                              [self.dataset._id, ], self.test._id)

            # Unicode encoding test
            model.status = model.STATUS_TRAINED
            model.save()
            unicode_string = u'Привет!'
            for row in _fake_raw_data:
                row['opening_id'] = row['opening_title'] = unicode_string
            self.db.TestExample.collection.remove(
                {'test_id': str(self.test2._id)})
            result = run_test([self.dataset._id, ], self.test2._id)
            self.assertEquals(result, 'Test completed')
            example = self.db.TestExample.find_one(
                {'test_id': str(self.test2._id)})
            self.assertEquals(example.id, unicode_string)
            self.assertEquals(example.name, unicode_string)


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
        self.assertEquals(example.data_input, {'data': 'value'})

    @patch('api.amazon_utils.AmazonEC2Helper.request_spot_instance',
           return_value=Mock(id='some_id')
           )
    def test_request_spot_instance(self, mock_request):
        from api.tasks import request_spot_instance

        model = self.db.Model.find_one()
        res = request_spot_instance('dataset_id', 'instance_type', model._id)

        model.reload()
        self.assertEquals(model.status, model.STATUS_REQUESTING_INSTANCE)
        self.assertEquals(res, 'some_id')
        self.assertEquals(model.spot_instance_request_id, res)

    @patch('api.amazon_utils.AmazonEC2Helper.get_instance',
           return_value=Mock(**{'private_ip_address': '8.8.8.8'}))
    @patch('api.tasks.train_model')
    def test_get_request_instance(self, mock_get_instance, mock_train):
        from api.tasks import get_request_instance

        model = self.db.Model.find_one()
        user = self.db.User.find_one()

        with patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance',
                   return_value=Mock(**{
                       'state': 'active',
                       'status.code': '200',
                       'status.message': 'Msg',
                   })):
            res = get_request_instance('some_id',
                         callback='train',
                         dataset_ids=['dataset_id'],
                         model_id=model._id,
                         user_id=user._id)
            self.assertEquals(res, '8.8.8.8')
            self.assertTrue(mock_train.apply_async)

            model.reload()
            self.assertEquals(model.status, model.STATUS_INSTANCE_STARTED)

    @patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance')
    def test_get_request_instance_failed(self, mock_request_instance):
        from api.tasks import get_request_instance, InstanceRequestingError

        model = self.db.Model.find_one()
        user = self.db.User.find_one()

        mock_request_instance.return_value = Mock(**{
            'state': 'failed',
            'status.code': 'bad-parameters',
            'status.message': 'Msg',
        })

        self.assertRaises(
            InstanceRequestingError,
            get_request_instance,
            'some_id',
            callback='train',
            dataset_ids=['dataset_id'],
            model_id=model._id,
            user_id=user._id
        )

        model.reload()
        self.assertEquals(model.status, model.STATUS_ERROR)
        self.assertEquals(model.error, 'Instance was not launched')

    @patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance')
    def test_get_request_instance_canceled(self, mock_request_instance):
        from api.tasks import get_request_instance

        model = self.db.Model.find_one()
        user = self.db.User.find_one()

        mock_request_instance.return_value = Mock(**{
            'state': 'canceled',
            'status.code': 'canceled',
            'status.message': 'Msg',
        })

        res = get_request_instance('some_id',
                         callback='train',
                         dataset_ids=['dataset_id'],
                         model_id=model._id,
                         user_id=user._id)
        self.assertIsNone(res)

        model.reload()
        self.assertEquals(model.status, model.STATUS_CANCELED)

    @patch('api.amazon_utils.AmazonEC2Helper.get_request_spot_instance')
    def test_get_request_instance_still_open(self, mock_request_instance):
        from celery.exceptions import RetryTaskError
        from api.tasks import get_request_instance

        model = self.db.Model.find_one()
        user = self.db.User.find_one()

        mock_request_instance.return_value = Mock(**{
            'state': 'open',
            'status.code': 'bad-parameters',
            'status.message': 'Msg',
        })

        self.assertRaises(
            RetryTaskError,
            get_request_instance,
            'some_id',
            callback='train',
            dataset_ids=['dataset_id'],
            model_id=model._id,
            user_id=user._id
        )

    @patch('api.amazon_utils.AmazonEC2Helper.terminate_instance')
    def test_terminate_instance(self, mock_terminate_instance):
        from api.tasks import terminate_instance
        terminate_instance('some task id', 'some instance id')
        mock_terminate_instance.assert_called_with('some instance id')

    @patch('api.amazon_utils.AmazonEC2Helper.cancel_request_spot_instance')
    def test_cancel_request_spot_instance(self,
                                          mock_cancel_request_spot_instance):
        from api.tasks import cancel_request_spot_instance
        model = self.db.Model.find_one()
        cancel_request_spot_instance('some req id', model._id)
        mock_cancel_request_spot_instance.assert_called_with('some req id')
        model.reload()
        self.assertEquals(model.status, model.STATUS_CANCELED)

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
