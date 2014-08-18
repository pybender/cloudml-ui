# -*- coding: utf8 -*-
import json
from mock import patch, MagicMock, Mock
from moto import mock_s3
from sqlalchemy import desc

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from views import TestResource, TestExampleResource
from models import TestResult, TestExample
from api.ml_models.models import Model
from api.ml_models.fixtures import ModelData, WeightData, SegmentData
from api.import_handlers.fixtures import ImportHandlerData, DataSetData
from api.import_handlers.models import DataSet, ImportHandler
from api.instances.models import Instance
from api.instances.fixtures import InstanceData
from api.async_tasks.models import AsyncTask
from tasks import run_test
from api.base.exceptions import InvalidOperationError
from fixtures import TestResultData, TestExampleData
from api.features.fixtures import FeatureSetData, FeatureData


IMPORT_PARAMS = json.dumps({'start': '2012-12-03',
                            'end': '2012-12-04',
                            'category': 'smth'})


class TestResourceTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the Test API. """
    BASE_URL = '/cloudml/models/{0!s}/tests/'
    RESOURCE = TestResource
    Model = TestResult
    datasets = [FeatureData, FeatureSetData, InstanceData, ImportHandlerData,
                DataSetData, ModelData, TestResultData, TestExampleData]

    def setUp(self):
        super(TestResourceTests, self).setUp()
        self.obj = self.Model.query.filter_by(
            name=TestResultData.test_01.name).one()
        self.handler = ImportHandler.query.first()
        self.model = Model.query.filter_by(
            name=ModelData.model_01.name).first()
        self.model.test_import_handler = self.handler
        self.model.save()

        self.BASE_URL = self.BASE_URL.format(self.obj.model.id)
        self.MODEL_PARAMS = {'model_id': self.obj.model.id}
        self.RELATED_PARAMS = {'test_result_id': self.obj.id,
                               'model_id': self.obj.model.id}
        self.instance = Instance.query.filter_by(
            name=InstanceData.instance_01.name).one()
        self.POST_DATA = {
            'aws_instance': self.instance.id,
            'existing_instance_selected': True,
            'new_dataset_selected': True
        }

    def test_list(self):
        self.check_list(show='', query_params=self.MODEL_PARAMS)
        self.check_list(show='name,status', query_params=self.MODEL_PARAMS)

    def test_details(self):
        self.check_details(show='')
        self.check_details(show='name,status')

    @patch('api.model_tests.tasks.calculate_confusion_matrix')
    def test_confusion_matrix(self, mock_calculate):
        url = self._get_url(
            id=self.obj.id,
            action='confusion_matrix',
            weight0=10,
            weight1=12,
        )
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        mock_calculate.delay.assert_called_once_with(
            self.obj.id,
            10.0,
            12.0
        )

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.model_tests.tasks.run_test')
    def test_post(self, mock_run_test, mock_multipart_upload):
        """
        Checks creating new Test with creating new dataset.
        """
        data = {'format': DataSet.FORMAT_JSON, 'parameters': IMPORT_PARAMS}
        data.update(self.POST_DATA)
        data, test = self.check_edit(data, load_json=True)

        self.assertEquals(test.status, test.STATUS_IMPORTED)
        self.assertTrue(test.name.startswith('Test'))
        model = self.model
        self.assertEquals(test.model_name, model.name)
        self.assertEquals(test.model, model)
        self.assertEquals(test.model_id, model.id)
        self.assertFalse(test.error)
        self.assertTrue(test.created_on)
        self.assertEquals(test.created_by.name, 'User-2')
        self.assertEquals(test.parameters, json.loads(IMPORT_PARAMS))

        # This info should be filled after completing running
        # run_test celery task, which is mocked
        self.assertFalse(test.examples_count)
        self.assertFalse(test.accuracy)
        self.assertFalse(test.classes_set)
        self.assertFalse(test.metrics)
        self.assertFalse(test.dataset)
        self.assertFalse(test.memory_usage)

        self.assertTrue(mock_multipart_upload.called,
                        'Loaded dataset should be uploaded to Amazon S3')

        instance = self.instance
        mock_run_test.subtask.assert_called_once_with(
            args=(test.id, ),
            options={'queue': instance.name})
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['id'], test.id)
        self.assertEquals(data[self.RESOURCE.OBJECT_NAME]['name'], test.name)

    @mock_s3
    @patch('api.amazon_utils.AmazonS3Helper.save_gz_file')
    @patch('api.model_tests.tasks.run_test')
    def test_post_csv(self, mock_run_test, mock_multipart_upload):
        """ Checks creating new Test with creating new dataset. """
        data = {'format': DataSet.FORMAT_CSV, 'parameters': IMPORT_PARAMS}
        data.update(self.POST_DATA)
        resp, test = self.check_edit(data)

        self.assertEquals(test.status, test.STATUS_IMPORTED)
        self.assertTrue(test.name.startswith('Test'))
        model = self.model
        self.assertEquals(test.model_name, model.name)
        self.assertEquals(test.model, model)
        self.assertEquals(test.model_id, self.model.id)
        self.assertFalse(test.error)

    @mock_s3
    @patch('api.model_tests.tasks.run_test')
    def test_post_with_dataset(self, mock_run_test):
        """ Tests creating new Test with specifying dataset. """
        dataset = DataSet.query.filter_by(
            name=DataSetData.dataset_01.name).first()
        data = {'dataset': dataset.id}
        data.update(self.POST_DATA)
        data['new_dataset_selected'] = False
        resp = self.client.post(self._get_url(), data=data,
                                headers=HTTP_HEADERS)
        data = json.loads(resp.data)
        self.assertEquals(resp.status_code, 201)

        test = TestResult.query.get(data[self.RESOURCE.OBJECT_NAME]['id'])
        self.assertEquals(test.status, test.STATUS_QUEUED)

        instance = Instance.query.get(self.instance.id)
        mock_run_test.apply_async.assert_called_once_with(
            ([dataset.id], test.id),
            queue=instance.name)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in data)

    def test_post_validation(self):
        """ Tests validation errors, when posting new Test. """
        data = {'spot_instance_type': 'INVALID',
                'existing_instance_selected': False,
                'new_dataset_selected': False}
        errors = {
            u'dataset': u'Please select Data Set',
            u'spot_instance_type': u'Should be one of m3.xlarge, m3.2xlarge, cc2.8xlarge, cr1.8xlarge, hi1.4xlarge, hs1.8xlarge'
        }
        self.check_edit_error(data, errors)

    def test_delete(self):
        count = TestResult.query.count()
        self.assertTrue(count > 1, "Invalid fixtures. Found %s tests" % count)
        count = TestExample.query.count()
        self.assertTrue(
            count > 1, "Invalid fixtures. Found %s examples" % count)

        self.check_delete()

        # Checks whether not all docs was deleted
        self.assertTrue(TestResult.query.count(),
                        "All tests was deleted!")
        self.assertTrue(TestExample.query.count(),
                        "All examples was deleted!")


class TestExampleResourceTests(BaseDbTestCase, TestChecksMixin):
    """ Tests of the Test Examples API. """
    RESOURCE = TestExampleResource
    Model = TestExample
    datasets = [FeatureData, FeatureSetData, ImportHandlerData,
                DataSetData, ModelData, WeightData,
                TestResultData, TestExampleData, SegmentData]

    def setUp(self):
        super(TestExampleResourceTests, self).setUp()
        self.test = TestResult.query.filter_by(
            name=TestResultData.test_01.name).one()
        self.model = self.test.model
        self.BASE_URL = '/cloudml/models/{0!s}/tests/{1!s}/examples/'.format(
            self.model.id, self.test.id
        )

        # TODO: investigate why does it help
        self.db.session.expire_all()

    def test_list(self):
        self.check_list(
            show='created_on,label,pred_label',
            query_params={'test_result': self.test})

        url = '{0}?{1}&{2}'.format(
            self.BASE_URL,
            'action=examples:list',
            'data_input.employer->country=United Kingdom',
            'show=id,name,label,pred_label,title,prob,example_id'
        )
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)

    def test_filter(self):
        def check_filter(data, count=None):
            if count is not None:
                query_params = None
            else:
                query_params = {'test_result': self.test}
                query_params.update(data)
            resp = self.check_list(
                data=data,
                show='label,pred_label,data_input',
                query_params=query_params,
                count=count)
            return resp

        check_filter({'pred_label': '1'})
        check_filter({'data_input->>opening_id': '201913099'}, count=4)
        resp = check_filter(
            {'data_input->>employer->country': 'USA'}, count=2)
        self.assertEquals(
            resp['test_examples'][0]['data_input']['employer->country'], 'USA')

    def test_ordering(self):
        def check_prob_order(data, prob_0):
            query_params = {'test_result': self.test}
            resp = self.check_list(
                    data=data,
                    show='prob',
                    query_params=query_params)

            actual_prob_0 = []
            actual_prob_1 = []
            for ex in resp['test_examples']:
                actual_prob_0.append(ex['prob'][0])
                actual_prob_1.append(ex['prob'][1])
            self.assertEquals(actual_prob_0, prob_0)
            prob_1 = [1 - prob for prob in prob_0]
            self.assertEquals(actual_prob_1, prob_1)

        # Note: we are checking ordering by prob_0
        # psql arrays have numeration from 1
        right_data = [0.6, 0.5, 0.1, 0.05]
        data = {
            'sort_by': 'prob[1]',
            'order': 'desc'}
        check_prob_order(
            data, right_data)

        data = {
            'sort_by': 'prob[1]',
            'order': 'asc'}
        right_data.reverse()
        check_prob_order(
            data, right_data)

    @mock_s3
    @patch('api.model_tests.models.TestResult.get_vect_data')
    @patch('api.ml_models.models.Model.get_trainer')
    def test_details_weight(self, mock_get_trainer, mock_get_vect_data):
        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(
            open('api/ml_models/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        mock_get_vect_data.return_value = [0.123, 0.0] * 500

        obj = self.test.examples[0]
        url = self._get_url(id=obj.id, show='id,name,weighted_data_input')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_trainer.called)
        data = json.loads(resp.data)['test_example']

        for key in ['css_class', 'model_weight', 'transformed_weight',
                    'value', 'vect_value', 'weight']:
            self.assertTrue(key in data['weighted_data_input']['opening_id'])

    def test_groupped(self):
        url = self._get_url(action='groupped',
                            field='opening_id', count='2')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEquals(data['field_name'], 'opening_id')
        item = data['test_examples']['items'][0]
        self.assertEquals(
            TestExample.query.filter_by(test_result=self.test).count(), 4,
            "Fixtures was changed")
        self.assertEquals(item['count'], 4)
        self.assertEquals(item['group_by_field'], '201913099')
        self.assertTrue(item['avp'] > 0)
        self.assertTrue(data['mavp'] > 0)

    def test_datafields(self):
        url = self._get_url(action='datafields')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEquals(data['fields'], ['employer->country', 'opening_id'])

    @patch('api.model_tests.tasks.get_csv_results')
    def test_csv(self, mock_get_csv):
        fields = 'name,id,label,pred_label,prob,data_input.employer->country'
        url = self._get_url(action='csv', show=fields)
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(mock_get_csv.delay.called)


class TasksTests(BaseDbTestCase):
    """ Tests celery tasks. """
    datasets = [DataSetData, TestResultData, TestExampleData]

    def setUp(self):
        super(TasksTests, self).setUp()
        self.test = TestResult.query.filter_by(name=TestResultData.test_01.name).one()
        self.test2 = TestResult.query.filter_by(name=TestResultData.test_02.name).one()
        self.dataset = DataSet.query.first()  # TODO:
        self.examples_count = TestExample.query.filter_by(
            test_result=self.test).count()

    def _set_probabilities(self, probabilities):
        for example in TestExample.query.all():
            params = probabilities.get(example.name)
            if params:
                label, prob = params
                example.test = self.test
                example.label = label
                example.prob = prob
                example.save()

    def test_calculate_confusion_matrix(self):
        from tasks import calculate_confusion_matrix

        def _assertMatrix(w0, w1, expected):
            result = calculate_confusion_matrix(self.test.id, w0, w1)
            result = zip(*result)[-1]
            self.assertEquals(result, expected)
            self.assertEquals(self.examples_count, sum([sum(row) for row in result]))

        self._set_probabilities({
            'Some Example #1-1':  ('0', [0.3, 0.7]),
            'Some Example #1-2': ('0', [0.9, 0.1]),
            'Some Example #1-3':  ('1', [0.3, 0.7]),
            'Some OtherModel Example #1-1':  ('1', [0.2, 0.8]),
        })

        _assertMatrix(1, 1, ([1, 1], [0, 2]))
        _assertMatrix(0.5, 0.5, ([1, 1], [0, 2]))

        _assertMatrix(1, 10, ([0, 2], [0, 2]))
        _assertMatrix(1, 100, ([0, 2], [0, 2]))
        _assertMatrix(10, 1, ([2, 0], [2, 0]))
        _assertMatrix(100, 1, ([2, 0], [2, 0]))
        _assertMatrix(0, 1, ([0, 2], [0, 2]))
        _assertMatrix(1, 0, ([2, 0], [2, 0]))
        _assertMatrix(1, 3, ([1, 1], [0, 2]))
        _assertMatrix(3, 1, ([2, 0], [1, 1]))

        self.assertRaises(ValueError, calculate_confusion_matrix, self.test.id, 0, 0)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test.id, -1, 1)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test.id, 1, -1)
        self.assertRaises(ValueError, calculate_confusion_matrix, 5646546, 1, 1)

    @mock_s3
    @patch('api.models.DataSet.get_data_stream')
    def test_get_csv_results(self, mock_get_data_stream):
        from tasks import get_csv_results

        fields = ['label', 'pred_label', 'prob']
        url = get_csv_results.delay(self.test.model.id, self.test.id, fields).get()

        self.assertTrue(url)

        # TODO: signals aren't called when CELERY_ALWAYS_EAGER == True. Update Celery?
        # task = AsyncTask.query.filter_by(
        #     task_name='api.model_tests.tasks.get_csv_results'
        # ).order_by(desc(AsyncTask.created_on)).first()
        # self.assertEqual(task.result, url)
        # self.assertEqual(task.status, AsyncTask.STATUS_COMPLETED)

    @mock_s3
    @patch('api.models.Model.get_trainer')
    @patch('api.models.DataSet.get_data_stream')
    def _check_run_test(self, test, metrics_mock_class, _fake_raw_data,
                        mock_get_data_stream, mock_get_trainer):
        mocks = [mock_get_data_stream, mock_get_trainer]
        import numpy
        import scipy

        if _fake_raw_data is None:
            _fake_raw_data = {"default": [{'application_id': '123',
                               'hire_outcome': '0',
                               'title': 'A1'}] * 100}

        def _fake_test(self, *args, **kwargs):
            _fake_test.called = True
            self._raw_data = _fake_raw_data
            metrics_mock = metrics_mock_class()
            preds = Mock()
            preds.size = 100
            preds.__iter__ = Mock(return_value=iter([0] * 100))
            metrics_mock._preds = preds

            metrics_mock._probs = [numpy.array([0.1, 0.2])] * 100

            metrics_mock._true_data = scipy.sparse.coo_matrix([[0, 0, 0]] * 100)

            return metrics_mock

        # Set up mock trainer
        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(
            open('./api/ml_models/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        with patch('core.trainer.trainer.Trainer.test',
                   _fake_test) as mock_test:
            mocks.append(mock_test)
            return run_test([self.dataset.id, ], test.id), mocks

    def test_run_test_with_untrained_model(self):
        model = self.test.model
        model.status = model.STATUS_NEW
        model.save()
        self.assertRaises(InvalidOperationError, run_test,
                          [self.dataset.id, ], self.test.id)

    def test_run_test_unicode_encoding(self):
        test = TestResult.query.filter_by(name=TestResultData.test_04.name).first()
        unicode_string = u'Привет!'
        _fake_raw_data = {'default': [{'application_id': '123',
                           'hire_outcome': '0',
                           'title': 'A1',
                           'opening_title': unicode_string,
                           'opening_id': unicode_string}] * 100 }
        
        result, mocks = self._check_run_test(test, MetricsMockBinaryClassifier, _fake_raw_data)
        self.assertEquals(result, 'Test completed')
        example = TestExample.query.filter_by(
            test_result=test).first()
        self.assertEquals(example.data_input.keys(), _fake_raw_data['default'][0].keys())
        self.assertEquals(
            example.data_input['opening_id'], unicode_string)
        self.assertEquals(example.example_id, unicode_string)
        self.assertEquals(example.name, unicode_string)

    def test_run_test(self):
        test = TestResult.query.filter_by(name=TestResultData.test_04.name).first()
        model = test.model
        self.assertEquals(model.status, model.STATUS_TRAINED, model.__dict__)

        self.assertEquals(
            TestExample.query.filter_by(test_result=test).count(), 0)

        result, mocks = self._check_run_test(test, MetricsMockBinaryClassifier, None)
        self.assertEquals(result, 'Test completed')
        mock_get_data_stream, mock_get_trainer, mock_run_test = mocks
        self.assertEquals(1, mock_get_data_stream.call_count,
                          'Should be cached and called only once')

        example = TestExample.query.filter_by(test_result=test).first()
        self.assertTrue(example.data_input, 'Raw data should be filled at all')
        self.assertEquals(example.data_input.keys(),
                          ['hire_outcome', 'application_id', 'title'])


    def test_run_test_ndim_classifier(self):
        test = TestResult.query.filter_by(name=TestResultData.test_04.name).first()
        model = test.model
        self.assertEquals(model.status, model.STATUS_TRAINED, model.__dict__)

        self.assertEquals(
            TestExample.query.filter_by(test_result=test).count(), 0)

        result, mocks = self._check_run_test(test, MetricsMockNDimClassifier, None)
        self.assertEquals(result, 'Test completed')
        mock_get_data_stream, mock_get_trainer, mock_run_test = mocks
        self.assertEquals(1, mock_get_data_stream.call_count,
                          'Should be cached and called only once')

        example = TestExample.query.filter_by(test_result=test).first()
        self.assertTrue(example.data_input, 'Raw data should be filled at all')
        self.assertEquals(example.data_input.keys(),
                          ['hire_outcome', 'application_id', 'title'])


class TasksRunTestTests(BaseDbTestCase):
    """
    Testing celery task run_test end-to-end with minimal mocking
    """
    datasets = [DataSetData, TestResultData, TestExampleData]
    def setUp(self):
        super(TasksRunTestTests, self).setUp()
        self.dataset = DataSet.query.first()

    @patch('api.models.Model.get_trainer')
    @patch('api.models.DataSet.get_data_stream')
    def run_real_test_binary_classifier(self, mock_get_data_stream, mock_get_trainer):
        test = TestResult.query.filter_by(name=TestResultData.test_04.name).first()
        self.assertEqual({}, test.metrics)
        self.assertEquals(test.model.status, test.model.STATUS_TRAINED, test.model.__dict__)

        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(open('./api/ml_models/model.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        import gzip
        mock_get_data_stream.return_value = gzip.open('./api/import_handlers/ds.gz', 'r')

        result = run_test([self.dataset.id, ], test.id)
        self.assertEqual(result, 'Test completed')
        self.assertEqual(2, len(test.classes_set))
        self.assertIsInstance(test.classes_set, list)

        # any new metric added, you should add corresponding asserts
        self.assertEqual(6, len(test.metrics.keys()))

        self.assertTrue(test.metrics.has_key('confusion_matrix'))
        self.assertEqual(len(test.classes_set), len(test.metrics['confusion_matrix']))
        for i, v in enumerate(test.metrics['confusion_matrix']):
            self.assertIsInstance(v, list, 'cofusion matrix @ index:%s is not tuple/list' % (i,))
            self.assertEqual(2, len(v))

        pos_label = test.classes_set[1]
        self.assertTrue(test.metrics.has_key('roc_curve'))
        self.assertIsInstance(test.metrics['roc_curve'], dict)
        self.assertTrue(test.metrics['roc_curve'].has_key(pos_label))
        self.assertEqual(2, len(test.metrics['roc_curve'][pos_label]))
        self.assertIsInstance(test.metrics['roc_curve'][pos_label][0], list)
        self.assertIsInstance(test.metrics['roc_curve'][pos_label][1], list)

        self.assertTrue(test.metrics.has_key('roc_auc'))
        self.assertTrue(test.metrics['roc_auc'].has_key(pos_label))
        self.assertIsInstance(test.metrics['roc_auc'][pos_label], float)

        self.assertTrue(test.metrics.has_key('accuracy'))
        self.assertIsInstance(test.metrics['accuracy'], float)

        self.assertTrue(test.metrics.has_key('avarage_precision'))
        self.assertIsInstance(test.metrics['avarage_precision'], float)

    @patch('api.models.Model.get_trainer')
    @patch('api.models.DataSet.get_data_stream')
    def run_real_test_multiclass_classifier(self, mock_get_data_stream, mock_get_trainer):
        test = TestResult.query.filter_by(name=TestResultData.test_04.name).first()
        self.assertEqual({}, test.metrics)
        self.assertEquals(test.model.status, test.model.STATUS_TRAINED, test.model.__dict__)

        from core.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(open('./api/ml_models/multiclass-trainer.dat', 'r').read())
        mock_get_trainer.return_value = trainer

        import gzip
        mock_get_data_stream.return_value = gzip.open('./api/import_handlers/multiclass_ds.gz', 'r')

        result = run_test([self.dataset.id, ], test.id)
        self.assertEqual(result, 'Test completed')
        self.assertEqual(3, len(test.classes_set))
        self.assertIsInstance(test.classes_set, list)

        # any new metric added, you should add corresponding asserts
        self.assertEqual(4, len(test.metrics.keys()))

        for pos_label in test.classes_set:
            self.assertTrue(test.metrics.has_key('roc_curve'))
            self.assertIsInstance(test.metrics['roc_curve'], dict)
            self.assertTrue(test.metrics['roc_curve'].has_key(pos_label))
            self.assertEqual(2, len(test.metrics['roc_curve'][pos_label]))
            self.assertIsInstance(test.metrics['roc_curve'][pos_label][0], list)
            self.assertIsInstance(test.metrics['roc_curve'][pos_label][1], list)

            self.assertTrue(test.metrics.has_key('roc_auc'))
            self.assertTrue(test.metrics['roc_auc'].has_key(pos_label))
            self.assertIsInstance(test.metrics['roc_auc'][pos_label], float)

        self.assertTrue(test.metrics.has_key('confusion_matrix'))
        self.assertEqual(len(test.classes_set), len(test.metrics['confusion_matrix']))
        for i, v in enumerate(test.metrics['confusion_matrix']):
            self.assertIsInstance(v, list, 'cofusion matrix @ index:%s is not tuple/list' % (i,))
            self.assertEqual(2, len(v))

        self.assertTrue(test.metrics.has_key('accuracy'))
        self.assertIsInstance(test.metrics['accuracy'], float)


class MetricsMockBinaryClassifier(MagicMock):
    accuracy = 0.85
    classes_set = ['a', 'b']
    classes_count = len(classes_set)
    _labels = ['a', 'b'] * 50

    def get_metrics_dict(self):
        return {
            'confusion_matrix': [0, 0],
            'roc_curve': {'b': [[0], [1]]},
            'roc_auc': {'b': 0.1},
            'precision_recall_curve': [[0], [0], [0], [0]],
        }


class MetricsMockNDimClassifier(MagicMock):
    accuracy = 0.85
    classes_set = ['a', 'b', 'c']
    classes_count = len(classes_set)
    _labels = ['a', 'b', 'c'] * 50

    def get_metrics_dict(self):
        return {
            'confusion_matrix': [0, 0, 0],
            'roc_curve': {'a': [[0], [1]], 'b': [[1], [0]], 'c': [[0], [0]]},
            'roc_auc': {'a': 0.2, 'b': 0.1}
        }
