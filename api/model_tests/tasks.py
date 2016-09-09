"""
Model tests related Celery tasks.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import os
import logging
import numpy
import csv
import uuid
from itertools import izip, repeat
from sqlalchemy.exc import SQLAlchemyError

from api import celery, app
from api.base.tasks import SqlAlchemyTask, TaskException, get_task_traceback
from api.base.exceptions import InvalidOperationError
from api.logs.logger import init_logger
from api.model_tests.models import TestResult, TestExample
from api.ml_models.models import Model, Weight
from api.import_handlers.models import DataSet
from api.models import PredefinedDataSource


@celery.task(base=SqlAlchemyTask)
def run_test(dataset_ids, test_id):
    """
    Running test for trained model.

    dataset_ids: list
        List of dataset ids used for testing model. Now only first one in the
        list used. (Multidataset testing hasn't implemented yet).
    model_id: int
        ID of the model to test.
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
        logging.info('Using {0} (id #{1}) dataset'.format(dataset.filename,
                                                          dataset.id))
        result = Model.run_test(model, dataset)

        metrics, raw_data = result
        logging.info("Memory usage: %f",
                     memory_usage(-1, interval=0, timeout=None)[0])
        metrics_dict = metrics.get_metrics_dict()
        if 'accuracy' in metrics_dict:
            test.accuracy = metrics.accuracy
            logging.info('Accuracy: %f', test.accuracy)

        # TODO: Refactor this. Here are possible issues with conformity
        # between labels and values
        if 'confusion_matrix' in metrics_dict:
            confusion_matrix = metrics_dict['confusion_matrix']
            confusion_matrix_ex = []
            for i, val in enumerate(metrics.classes_set):
                confusion_matrix_ex.append((str(val), confusion_matrix[i]))
            metrics_dict['confusion_matrix'] = confusion_matrix_ex

        if 'precision_recall_curve' in metrics_dict:
            n = len(metrics._labels) / 100 or 1
            if metrics.classes_count == 2:
                metrics_dict['precision_recall_curve'][1] = \
                    metrics_dict['precision_recall_curve'][1][0::n]
                metrics_dict['precision_recall_curve'][0] = \
                    metrics_dict['precision_recall_curve'][0][0::n]

        if 'roc_curve' in metrics_dict:
            n = len(metrics._labels) / 100 or 1
            calc_range = [1] if metrics.classes_count == 2 \
                else range(len(metrics.classes_set))
            for i in calc_range:
                label = metrics.classes_set[i]
                sub_fpr = metrics_dict['roc_curve'][label][0][0::n]
                sub_tpr = metrics_dict['roc_curve'][label][1][0::n]
                metrics_dict['roc_curve'][label] = [sub_fpr, sub_tpr]

        if 'roc_curve' in metrics_dict:
            test.roc_auc = metrics_dict.pop('roc_auc')
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
        # lock dataset used for testing
        dataset.locked = True
        dataset.save()

        test.examples_count = all_count
        test.memory_usage = memory_usage(-1, interval=0, timeout=None)[0]

        vect_data = metrics._true_data
        from bson import Binary
        test.save()

        def fill_weights(trainer, test, segment):
            for clazz, weights in trainer.get_weights(
                    segment.name).iteritems():
                positive = weights['positive']
                negative = weights['negative']

                def process_weights(weight_list):
                    for weight_dict in weight_list:
                        weight = Weight.query.filter_by(
                            model=model,
                            segment=segment,
                            class_label=str(clazz),
                            name=weight_dict['name']).one()
                        if weight.test_weights is not None:
                            test_weights = weight.test_weights.copy()
                        else:
                            test_weights = {}
                        test_weights[test_id] = weight_dict['feature_weight']
                        weight.test_weights = test_weights
                        weight.save(commit=False)
                        app.sql_db.session.add(weight)
                process_weights(positive)
                process_weights(negative)

        # Filling test weights
        if test.fill_weights:
            trainer = model.get_trainer()
            for segment in model.segments:
                logging.info(
                    'Storing test feature weights for segment %s',
                    segment.name)
                fill_weights(trainer, test, segment)

        data = []
        for segment, d in raw_data.iteritems():
            data = data + d

        logging.info('Storing test examples')
        if metrics._probs is None:
            probs = list(repeat(None, len(data)))
        else:
            probs = metrics._probs
        examples = izip(range(len(data)),
                        data,
                        metrics._labels,
                        metrics._preds,
                        probs)
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
        if isinstance(exc, SQLAlchemyError):
            app.sql_db.session.rollback()
        logging.error('Got exception when test model: {0} \n {1}'
                      .format(exc.message, get_task_traceback(exc)))
        test.status = test.STATUS_ERROR
        error_column_size = TestResult.error.type.length
        str_exc = str(exc)
        msg = ' ... TRUNCATED'
        test.error = str_exc if len(str_exc) <= error_column_size else \
            (str_exc[:error_column_size - len(msg)] + msg)
        test.save()
        raise TaskException(exc.message, exc)
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

    example_id = ndata.get(model.example_id, None) or \
        data.get(model.example_id, TestExample.NOT_FILED_ID)
    try:
        example.example_id = str(example_id)
    except UnicodeEncodeError:
        example.example_id = example_id.encode('utf-8')

    example_name = ndata.get(model.example_label, None) or \
        data.get(model.example_label, TestExample.NONAME)
    try:
        example.name = str(example_name)
    except UnicodeEncodeError:
        example.name = example_name.encode('utf-8')

    example.pred_label = str(pred)
    example.label = str(label)
    example.prob = prob.tolist() if prob is not None else None

    # Denormalized fields. TODO: move denormalization to TestExample model
    example.test_name = test.name
    example.model_name = model.name

    example.model = model
    example.test_result = test

    new_row = ndata
    example.data_input = ndata

    example.save(commit=False)
    return example, new_row


@celery.task(base=SqlAlchemyTask)
def calculate_confusion_matrix(test_id, weights):
    """
    Calculate confusion matrix for test with weights.

    test_id: int
        ID of the model test.
    weights: list of tuples (label, weight)
        where label - test.model.label - class label
        weight: positive float class weight

    Note:
    Now we support calculating confusion matrix for
    binary and multi class classifiers.
    """
    log_id = test_id
    from api.async_tasks.models import AsyncTask
    if calculate_confusion_matrix.request.id is not None:
        tasks = AsyncTask.query\
            .filter_by(task_id=calculate_confusion_matrix.request.id).limit(1)
        log_id = tasks[0].id

    init_logger('confusion_matrix_log', obj=int(log_id))
    logging.info('Starting re-calculating confusion matrix')
    logging.info('Checking confusion matrix weights')
    all_zero = True
    for weight in weights:
        if weight[1] != 0:
            all_zero = False
        if weight[1] < 0:
            logging.error("Negative weights found")
            raise ValueError('Negative weights are not allowed')

    if all_zero:
        logging.error("All weights are zero")
        raise ValueError('All weights can not be 0')

    test = TestResult.query.get(test_id)
    if test is None:
        logging.error('Test with id {0!s} not found!'.format(test_id))
        raise ValueError('Test with id {0!s} not found!'.format(test_id))

    if test.status != TestResult.STATUS_COMPLETED:
        logging.error('Test is not completed! Please wait and try again')
        raise ValueError('Test is not completed!')

    model = test.model
    if model is None:
        logging.error('Model with id {0!s} not found!'.format(
            test.model_id))
        raise ValueError('Model with id {0!s} not found!'.format(
            test.model_id))

    logging.info('Start calculating confusion matrix for test id {0!s}, '
                 'log id {1} with weights {2}'.format(
                     test_id, log_id, weights))

    dim = len(weights)
    matrix = [[0 for x in range(dim)] for x in range(dim)]

    i = 1
    for example in test.examples:
        true_value_idx = model.labels.index(example.label)

        weighted_sum = 0
        for weight in weights:
            index = model.labels.index(weight[0])
            weighted_sum += weight[1] * example.prob[index]

        if weighted_sum == 0:
            import json
            logging.error("Weighted sum is 0 on calculating test example #{0} "
                          "(probabilities: {1})"
                          .format(i, json.dumps(example.prob)))
            raise ValueError("Weighted sum is 0. Try another weights "
                             "or retest model.")

        weighted_prob = []
        for weight in weights:
            index = model.labels.index(weight[0])
            weighted_prob.append(
                weight[1] * example.prob[index] / weighted_sum)

        predicted = weighted_prob.index(max(weighted_prob))
        matrix[true_value_idx][predicted] += 1
        if i % 500 == 0:
            logging.info("{0} test examples processed".format(i))
        i += 1

    logging.info("Confusion matrix calculation completed")

    return zip(model.labels, matrix)


@celery.task(base=SqlAlchemyTask)
def export_results_to_db(model_id, test_id,
                         datasource_id, table_name, fields):
    """
    Export model test examples data to PostgreSQL db.

    model_id: int
        ID of the model
    test_id: int
        ID of the test, which examples it planned to export.
    datasource_id: int
        ID of datasource, which would be used to connect to PostgreSQL db.
    table_name: string
        Name of the table
    fields: list of string
        List of field names from TestExample to export to the database.
    """
    import psycopg2
    import psycopg2.extras
    init_logger('runtest_log', obj=int(test_id))

    test = TestResult.query.filter_by(
        model_id=model_id, id=test_id).first()
    if not test:
        logging.error('Test not found')
        return

    datasource = PredefinedDataSource.query.get(datasource_id)
    if not datasource:
        logging.error('Datasource not found')
        return

    db_fields = []
    for field in fields:
        if 'prob' == field:
            for label in test.classes_set:
                db_fields.append("prob_%s varchar(25)" % label)
        else:
            db_fields.append("%s varchar(25)" % field.replace('->', '__'))

    logging.info('Creating db connection %s' % datasource.db)
    conn = psycopg2.connect(datasource.db['conn'])
    query = "drop table if exists %s;" % table_name
    cursor = conn.cursor().execute(query)
    logging.info('Creating table %s' % table_name)
    query = "CREATE TABLE %s (%s);" % (table_name, ','.join(db_fields))
    cursor = conn.cursor().execute(query)

    count = 0
    for example in TestExample.get_data(test_id, fields):
        rows = []
        if count % 10 == 0:
            logging.info('Processed %s rows so far' % (count, ))
        for field in fields:
            if field == '_id':
                field = 'id'
            if field == 'id':
                field = 'example_id'
            val = example[field] if field in example else ''
            if field == 'prob':
                rows += val
            else:
                rows.append(val)
        rows = map(lambda x: "'%s'" % x, rows)
        query = "INSERT INTO %s VALUES (%s)" % (table_name, ",".join(rows))
        cursor = conn.cursor().execute(query)
        count += 1
    conn.commit()
    logging.info('Export completed.')

    return


@celery.task(base=SqlAlchemyTask)
def get_csv_results(model_id, test_id, fields):
    """
    Get test classification results in csv format and saves file
    to Amazon S3.

    model_id: int
        ID of the model
    test_id: int
        ID of the test, which examples it planned to export.
    fields: list of string
        List of field names from TestExample to export to csv file.
    """
    from api.amazon_utils import AmazonS3Helper

    def generate(test, name):
        from api.base.io_utils import get_or_create_data_folder
        path = get_or_create_data_folder()
        filename = os.path.join(path, name)
        header = list(fields)
        if 'prob' in header:
            prob_index = header.index('prob')
            for label in reversed(test.classes_set):
                header.insert(prob_index, 'prob_%s' % label)
            header.remove('prob')

        with open(filename, 'w') as fp:
            writer = csv.writer(fp, delimiter=',',
                                quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            for example in TestExample.get_data(test_id, fields):
                rows = []
                for field in fields:
                    if field == '_id':
                        field = 'id'
                    if field == 'id':
                        field = 'example_id'
                    val = example[field] if field in example else ''
                    if field == 'prob':
                        rows += val
                    else:
                        rows.append(val)
                writer.writerow(rows)
        return filename

    init_logger('runtest_log', obj=int(test_id))

    test = TestResult.query.filter_by(model_id=model_id, id=test_id).first()
    if test is None:
        logging.error('Test not found')
        return

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
