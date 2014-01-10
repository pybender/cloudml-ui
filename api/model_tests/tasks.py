import os
import logging
import csv
import uuid
from os import makedirs
from itertools import izip
from bson.objectid import ObjectId
from os.path import exists
from datetime import timedelta, datetime

from api import celery, app
from api.amazon_utils import AmazonS3Helper
from api.base.exceptions import InvalidOperationError
from api.logs.logger import init_logger
from api.model_tests.models import TestResult, TestExample
from api.ml_models.models import Model
from api.import_handlers.models import DataSet


@celery.task
def run_test(dataset_ids, test_id):
    """
    Running tests for trained model
    """
    init_logger('runtest_log', obj=int(test_id))

    test = TestResult.query.get(test_id)
    datasets = DataSet.query.filter(DataSet.id.in_(dataset_ids)).all()
    dataset = datasets[0]
    model = test.model

    try:
        if model.status != model.STATUS_TRAINED:
            raise InvalidOperationError("Train the model before")

        test.status = test.STATUS_IN_PROGRESS
        test.error = ""
        test.save()

        logging.info('Getting metrics and raw data')
        from memory_profiler import memory_usage
        mem_usage, result = memory_usage((Model.run_test, (model, dataset, )),
                                         interval=0, retval=True)
        metrics, raw_data = result
        test.accuracy = metrics.accuracy
        logging.info('Accuracy: %f', test.accuracy)
        logging.info("Memory usage: %f",
                     memory_usage(-1, interval=0, timeout=None)[0])
        metrics_dict = metrics.get_metrics_dict()

        # TODO: Refactor this. Here are possible issues with conformity
        # between labels and values
        confusion_matrix = metrics_dict['confusion_matrix']
        confusion_matrix_ex = []
        for i, val in enumerate(metrics.classes_set):
            confusion_matrix_ex.append((str(val), confusion_matrix[i]))
        metrics_dict['confusion_matrix'] = confusion_matrix_ex

        n = len(metrics._labels) / 100 or 1
        metrics_dict['roc_curve'][1] = metrics_dict['roc_curve'][1][0::n]
        metrics_dict['roc_curve'][0] = metrics_dict['roc_curve'][0][0::n]
        metrics_dict['precision_recall_curve'][1] = \
            metrics_dict['precision_recall_curve'][1][0::n]
        metrics_dict['precision_recall_curve'][0] = \
            metrics_dict['precision_recall_curve'][0][0::n]
        test.metrics = metrics_dict
        test.classes_set = list(metrics.classes_set)
        test.status = TestResult.STATUS_STORING

        if not model.comparable:
            # TODO: fix this
            model = Model.query.get(model.id)
            model.comparable = True
            model.save()

        all_count = metrics._preds.size
        test.dataset = dataset
        test.examples_count = all_count
        test.memory_usage = max(mem_usage)

        vect_data = metrics._true_data
        from bson import Binary
        import pickle
        test.vect_data = pickle.dumps(vect_data)

        test.save()

        logging.info('Storing test examples')
        examples = izip(range(len(raw_data)),
                        raw_data,
                        metrics._labels,
                        metrics._preds,
                        metrics._probs)
        logging.info("Memory usage: %f",
                     memory_usage(-1, interval=0, timeout=None)[0])

        for n, row, label, pred, prob in examples:
            if n % (all_count / 10) == 0:
                if all_count > 0:
                    app.sql_db.session.commit()
                logging.info('Processed %s rows so far' % n)

            example, new_row = _add_example_to_db(
                test, row, label, pred, prob, n)
            # test.examples_size += (get_doc_size(example) / 1024.0 / 1024.0)
            # example_ids.append(str(example.id))
        app.sql_db.session.commit()

        test.status = TestResult.STATUS_COMPLETED
        test.save()
        logging.info('Test %s completed' % test.name)

    except Exception, exc:
        logging.exception('Got exception when tests model')
        test.status = test.STATUS_ERROR
        test.error = str(exc)
        test.save()
        raise
    return 'Test completed'


def _add_example_to_db(test, data, label, pred, prob, num):
    """
    Adds info about Test Example to PostgreSQL.
    Returns created TestExampleSql object and data.
    """

    ndata = dict([(key.replace('.', '->'), val)
                 for key, val in data.iteritems()])
    model = test.model
    example = TestExample()
    example.num = num
    example_id = ndata.get(model.example_id, '-1')
    try:
        example.example_id = str(example_id)
    except UnicodeEncodeError:
        example.example_id = example_id.encode('utf-8')

    example_name = ndata.get(model.example_label, 'noname')
    try:
        example.name = str(example_name)
    except UnicodeEncodeError:
        example.name = example_name.encode('utf-8')

    example.pred_label = str(pred)
    example.label = str(label)
    example.prob = prob.tolist()

    # Denormalized fields. TODO: move denormalization to TestExample model
    example.test_name = test.name
    example.model_name = model.name

    example.model = model
    example.test_result = test

    new_row = ndata
    example.data_input = ndata

    example.save(commit=False)
    return example, new_row


@celery.task
def calculate_confusion_matrix(test_id, weight0, weight1):
    """
    Calculate confusion matrix for test.
    """
    init_logger('confusion_matrix_log', obj=int(test_id))

    if weight0 == 0 and weight1 == 0:
        raise ValueError('Both weights can not be 0')

    if weight0 < 0 or weight1 < 0:
        raise ValueError('Negative weights are not allowed')

    test = TestResult.query.get(test_id)
    if test is None:
        raise ValueError('Test with id {0!s} not found!'.format(test_id))

    model = test.model
    if model is None:
        raise ValueError('Model with id {0!s} not found!'.format(
            test.model_id))

    logging.info('Calculating confusion matrix for test id {!s}'.format(
        test_id))

    matrix = [[0, 0],
              [0, 0]]

    for example in test.examples:
        true_value_idx = model.labels.index(example.label)

        prob0, prob1 = example.prob[:2]

        weighted_sum = weight0 * prob0 + weight1 * prob1
        weighted_prob0 = weight0 * prob0 / weighted_sum
        weighted_prob1 = weight1 * prob1 / weighted_sum

        predicted = [weighted_prob0, weighted_prob1].index(
            max([weighted_prob0, weighted_prob1]))
        matrix[true_value_idx][predicted] += 1

    return zip(model.labels, matrix)


@celery.task
def get_csv_results(model_id, test_id, fields):
    """
    Get test classification results using csv format.
    """
    def generate(test, name):
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        filename = os.path.join(path, name)

        with open(filename, 'w') as fp:
            writer = csv.writer(fp, delimiter=',',
                                quoting=csv.QUOTE_ALL)
            writer.writerow(fields)
            for example in TestExample.get_data(test_id, fields):
                rows = []
                for field in fields:
                    if field == '_id':
                        field = 'id'
                    if field == 'id':
                        field = 'example_id'
                    val = example[field] if field in example else ''
                    rows.append(val)
                writer.writerow(rows)
        return filename

    init_logger('runtest_log', obj=int(test_id))

    test = TestResult.query.filter_by(model_id=model_id, id=test_id).first()
    if not test:
        logging.error('Test not found')
        return None

    name = 'Examples-{0!s}.csv'.format(uuid.uuid1())
    expires = 60 * 60 * 24 * 7  # 7 days

    logging.info('Creating file {0}...'.format(name))

    s3 = AmazonS3Helper()
    filename = generate(test, name)
    logging.info('Uploading file {0} to s3...'.format(filename))
    s3.save_key(name, filename, {
        'model_id': model_id,
        'test_id': test_id}, compressed=False)
    s3.close()
    os.remove(filename)
    url = s3.get_download_url(name, expires)

    return url
