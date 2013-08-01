import os
import json
import logging
import csv
import uuid
from itertools import izip
from bson.objectid import ObjectId
from os.path import exists
from os import makedirs, system
from datetime import timedelta, datetime
from boto.exception import EC2ResponseError
from celery.canvas import group

from api import celery, app
from api.models import Test, Model
from api.logger import init_logger
from api.amazon_utils import AmazonEC2Helper, AmazonS3Helper
from core.trainer.trainer import Trainer
from core.trainer.config import FeatureModel
from core.trainer.streamutils import streamingiterload


class InvalidOperationError(Exception):
    pass


@celery.task
def request_spot_instance(dataset_id=None, instance_type=None, model_id=None):
    init_logger('trainmodel_log', obj=model_id)

    model = app.db.Model.find_one({'_id': ObjectId(model_id)})
    model.status = model.STATUS_REQUESTING_INSTANCE
    model.save()

    try:
        ec2 = AmazonEC2Helper()
        logging.info('Request spot instance type: %s' % instance_type)
        request = ec2.request_spot_instance(instance_type)
        logging.info('Request id: %s:' % request.id)
    except EC2ResponseError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)

    model.spot_instance_request_id = request.id
    model.save()

    return request.id


@celery.task()
def get_request_instance(request_id,
                         callback=None,
                         dataset_id=None,
                         model_id=None):
    init_logger('trainmodel_log', obj=model_id)
    ec2 = AmazonEC2Helper()
    logging.info('Get spot instance request %s' % request_id)

    model = app.db.Model.find_one({'_id': ObjectId(model_id)})

    try:
        request = ec2.get_request_spot_instance(request_id)
    except EC2ResponseError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)

    if request.state == 'open':
        logging.info('Instance was not ran. Status: %s . Retry in 10s.' % request.state)
        raise get_request_instance.retry(countdown=app.config['REQUESTING_INSTANCE_COUNTDOWN'],
                                         max_retries=app.config['REQUESTING_INSTANCE_MAX_RETRIES'])

    if request.state == 'canceled':
        logging.info('Instance was canceled.')
        model.status = model.STATUS_CANCELED
        model.save()
        return None

    if request.state != 'active':
        logging.info('Instance was not launched. State is {0!s}, status is {1!s}, {2!s}.'.format(
            request.state, request.status.code, request.status.message))
        model.set_error('Instance was not launched')
        raise Exception('Instance was not launched')

    model.status = model.STATUS_INSTANCE_STARTED
    model.save()

    logging.info('Get instance %s' % request.instance_id)
    instance = ec2.get_instance(request.instance_id)
    logging.info('Instance %s(%s) lunched' %
            (instance.id,
             instance.private_ip_address))
    instance.add_tag('Name', 'cloudml-worker-auto')
    instance.add_tag('Owner', 'papadimitriou,nmelnik')
    instance.add_tag('Model_id', model_id)
    instance.add_tag('whoami', 'cloudml')

    if callback == "train":
        logging.info('Train model task apply async')
        queue = "ip-%s" % "-".join(instance.private_ip_address.split('.'))
        train_model.apply_async((dataset_id,
                                 model_id),
                                 queue=queue,
                                 link=terminate_instance.subtask(kwargs={'instance_id': instance.id}),
                                 link_error=terminate_instance.subtask(kwargs={'instance_id': instance.id})
                                )
    return instance.private_ip_address


@celery.task
def terminate_instance(task_id=None, instance_id=None):
    ec2 = AmazonEC2Helper()
    ec2.terminate_instance(instance_id)
    logging.info('Instance %s terminated' % instance_id)


@celery.task
def self_terminate(result=None):
    logging.info('Instance will be terminated')
    system("halt")


@celery.task
def cancel_request_spot_instance(request_id, model_id):
    init_logger('trainmodel_log', obj=model_id)
    model = app.db.Model.find_one({'_id': ObjectId(model_id)})

    logging.info('Cancelling spot instance request {0!s} for model id {1!s}...'.format(
        request_id, model_id))

    try:
        AmazonEC2Helper().cancel_request_spot_instance(request_id)
        logging.info('Spot instance request {0!s} has been cancelled for model id {1!s}'.format(
            request_id, model_id))
        model.status = model.STATUS_CANCELED
        model.save()
    except EC2ResponseError as e:
        model.set_error(e.error_message)
        raise Exception(e.error_message)


@celery.task
def import_data(dataset_id, model_id=None, test_id=None):
    """
    Import data from database.
    """
    from core.importhandler.importhandler import ExtractionPlan, ImportHandler
    try:
        dataset = app.db.DataSet.find_one({'_id': ObjectId(dataset_id)})
        importhandler = app.db.ImportHandler.find_one(
            {'_id': ObjectId(dataset.import_handler_id)})
        if dataset is None or importhandler is None:
            raise ValueError('DataSet or Import Handler not found')
        obj = None
        if not model_id is None:
            obj = app.db.Model.find_one({'_id': ObjectId(model_id)})
        if not test_id is None:
            obj = app.db.Test.find_one({'_id': ObjectId(test_id)})

        if obj:
            obj.status = obj.STATUS_IMPORTING
            obj.save()
        init_logger('importdata_log', obj=dataset_id)
        logging.info('Loading dataset %s' % dataset._id)

        import_start_time = datetime.now()

        logging.info("Import dataset using import handler '%s' \
with%s compression", importhandler.name, '' if dataset.compress else 'out')
        handler = json.dumps(importhandler.data)
        plan = ExtractionPlan(handler, is_file=False)
        handler = ImportHandler(plan, dataset.import_params)
        logging.info('The dataset will be stored to file %s', dataset.filename)
        handler.store_data_json(dataset.filename, dataset.compress)
        logging.info('Import dataset completed')

        logging.info('Retrieving data fields')
        row = None
        with dataset.get_data_stream() as fp:
            row = next(fp)
        if row:
            dataset.data_fields = json.loads(row).keys()
        logging.info('Dataset fields: {0!s}'.format(dataset.data_fields))

        logging.info('Saving file to Amazon S3')
        dataset.save_to_s3()
        logging.info('File saved to Amazon S3')

        dataset.status = dataset.STATUS_IMPORTED
        if obj:
            obj.status = obj.STATUS_IMPORTED
            obj.save()

        dataset.filesize = long(os.path.getsize(dataset.filename))
        dataset.records_count = handler.count
        dataset.time = (datetime.now() - import_start_time).seconds

        dataset.save(validate=True)

        logging.info('DataSet was loaded')
    except Exception, exc:
        logging.exception('Got exception when import dataset')
        dataset.set_error(exc)
        if obj:
            obj.set_error(exc)
        raise

    logging.info("Dataset using %s imported.", importhandler.name)
    return dataset_id


@celery.task
def train_model(dataset_id, model_id):
    """
    Train new model celery task.
    """
    init_logger('trainmodel_log', obj=model_id)

    try:
        model = app.db.Model.find_one({'_id': ObjectId(model_id)})
        dataset = app.db.DataSet.find_one({'_id': ObjectId(dataset_id)})
        model.delete_metadata()

        model.dataset = dataset
        model.status = model.STATUS_TRAINING
        model.error = ""
        model.save(validate=True)
        feature_model = FeatureModel(json.dumps(model.features),
                                     is_file=False)
        trainer = Trainer(feature_model)
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        train_fp = dataset.get_data_stream()

        from memory_profiler import memory_usage
        mem_usage = memory_usage((trainer.train, (streamingiterload(train_fp),)), interval=0)

        train_fp.close()
        trainer.clear_temp_data()

        model.status = model.STATUS_TRAINED
        model.set_trainer(trainer)
        model.memory_usage['training'] = max(mem_usage)
        model.save()

        fill_model_parameter_weights.delay(str(model._id))
    except Exception, exc:
        logging.exception('Got exception when train model')
        model.status = model.STATUS_ERROR
        model.error = str(exc)
        model.save()
        raise

    msg = "Model trained at %s" % trainer.train_time
    logging.info(msg)
    return msg


@celery.task
def fill_model_parameter_weights(model_id, reload=False):
    """
    Adds model parameters weights to db.
    """
    init_logger('trainmodel_log', obj=model_id)
    logging.info("Starting to fill model weights")
    try:
        model = app.db.Model.find_one({'_id': ObjectId(model_id)})
        if model is None:
            raise ValueError('Model not found: %s' % model_id)

        weights = model.get_trainer().get_weights()
        positive = weights['positive']
        negative = weights['negative']
        if reload:
            params = {'model_id': model_id}
            app.db.WeightsCategory.collection.remove(params)
            app.db.Weight.collection.remove(params)
        weights = app.db.Weight.find({'model_id': model_id})
        count = weights.count()
        if count > 0:
            raise InvalidOperationError('Weights for model %s already \
    filled: %s' % (model_id, count))

        from helpers.weights import calc_weights_css
        positive_weights = []
        negative_weights = []
        if len(positive) > 0:
            positive_weights = calc_weights_css(positive, 'green')
        if len(negative) > 0:
            negative_weights = calc_weights_css(negative, 'red')
        weight_list = positive_weights + negative_weights
        weight_list.sort(key=lambda a: abs(a['weight']))
        weight_list.reverse()

        # Adding weights and weights categories to db
        category_names = []
        for weight in weight_list:
            name = weight['name']
            splitted_name = name.split('->')
            long_name = ''
            count = len(splitted_name)
            for i, sname in enumerate(splitted_name):
                parent = long_name
                long_name = '%s.%s' % (long_name, sname) \
                            if long_name else sname
                params = {'model_name': model.name,
                          'model_id': model_id,
                          'parent': parent,
                          'short_name': sname}
                if i == (count - 1):
                    params.update({'name': weight['name'],
                                   'value': weight['weight'],
                                   'is_positive': bool(weight['weight'] > 0),
                                   'css_class': weight['css_class']})
                    weight = app.db.Weight(params)
                    weight.save(validate=True, check_keys=False)
                else:
                    if sname not in category_names:
                        # Adding a category, if it has not already added
                        category_names.append(sname)
                        params.update({'name': long_name})
                        category = app.db.WeightsCategory(params)
                        category.save(validate=True, check_keys=False)

        model.weights_synchronized = True
        model.save()
        msg = 'Model %s parameters weights was added to db: %s' % \
            (model.name, len(weight_list))
        logging.info(msg)
    except Exception, exc:
        logging.exception('Got exception when fill_model_parameter')
        raise
    return msg


@celery.task
def run_test(dataset_id, test_id):
    """
    Running tests for trained model
    """
    init_logger('runtest_log', obj=test_id)

    test = app.db.Test.find_one({'_id': ObjectId(test_id)})
    dataset = app.db.DataSet.find_one({'_id': ObjectId(dataset_id)})
    test.dataset = dataset
    model = test.model
    try:
        if model.status != model.STATUS_TRAINED:
            raise InvalidOperationError("Train the model before")

        test.status = test.STATUS_IN_PROGRESS
        test.error = ""
        test.save()

        # Caching data into temp file
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        name = 'Test_raw_data-{0!s}.dat'.format(uuid.uuid1())
        filename = os.path.join(path, name)
        with open(filename, 'w') as fp:
            fp.write(str(dataset.get_data_stream().read()))

        from memory_profiler import memory_usage
        mem_usage, result = memory_usage((Model.run_test, (model, filename, )),
                                         interval=0, retval=True)
        metrics = result
        test.accuracy = metrics.accuracy

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
        test.status = Test.STATUS_COMPLETED

        if not model.comparable:
            # TODO: fix this
            model = app.db.Model.find_one({'_id': model._id})
            model.comparable = True
            model.save()

        all_count = metrics._preds.size
        test.examples_count = all_count
        test.memory_usage['testing'] = max(mem_usage)
        test.save()

        def _chunks(sequences, n):
            for i in xrange(0, len(sequences[0]), n):
                yield [s[i:i+n] for s in sequences]

        examples = [
            range(dataset.records_count),  # indexes
            metrics._labels,
            metrics._preds.tolist(),
            metrics._probs.tolist(),
            [v.tolist() for v in metrics._true_data.todense()]
        ]

        examples_tasks = []
        for params in _chunks(examples, app.config['EXAMPLES_CHUNK_SIZE']):
            examples_tasks.append(store_examples.si(test_id, filename, params))

        # Wait for all results
        res = group(examples_tasks).apply_async().get()
        os.remove(filename)

    except Exception, exc:
        logging.exception('Got exception when tests model')
        test.status = test.STATUS_ERROR
        test.error = str(exc)
        test.save()
        raise
    return 'Test completed'


@celery.task
def store_examples(test_id, filename, params):
    res = []

    test = app.db.Test.find_one({'_id': ObjectId(test_id)})
    model = test.model

    with open(filename, 'r') as fp:
        row_nums = params[0]
        for r in range(row_nums[0]):  # First row_num
            fp.readline()

        for row_num, label, pred, prob, vectorized_data in izip(*params):
            row = fp.readline()
            row = json.loads(row)

            row = decode(row)
            new_row = {}
            for key, val in row.iteritems():
                new_key = key.replace('.', '->')
                new_row[new_key] = val

            example = app.db.TestExample()
            example['data_input'] = new_row
            example['vect_data'] = vectorized_data[0]
            example['id'] = str(row.get(model.example_id, '-1'))
            example['name'] = str(row.get(model.example_label, 'noname'))
            example['label'] = str(label)
            example['pred_label'] = str(pred)
            example['prob'] = prob
            example['test_name'] = test.name
            example['model_name'] = model.name
            example['test_id'] = str(test._id)
            example['model_id'] = str(model._id)
            try:
                example.validate()
            except Exception, exc:
                logging.error('Problem with saving example #%s: %s',
                              row_num, exc)
                res.append((None, None))
            example.save(check_keys=False)

            res.append((row_num, str(example._id)))

    return res


@celery.task
def calculate_confusion_matrix(test_id, weight0, weight1):
    """
    Calculate confusion matrix for test.
    """
    init_logger('confusion_matrix_log', obj=test_id)

    if weight0 == 0 and weight1 == 0:
        raise ValueError('Both weights can not be 0')

    test = app.db.Test.find_one({'_id': ObjectId(test_id)})
    if test is None:
        raise ValueError('Test with id {0!s} not found!'.format(test_id))

    logging.info('Calculating confusion matrix for test id {!s}'.format(test_id))

    model = app.db.Model.find_one({'_id': ObjectId(test['model_id'])})
    if model is None:
        raise ValueError('Model with id {0!s} not found!'.format(test['model_id']))

    matrix = [[0, 0],
              [0, 0]]

    for example in app.db.TestExample.find({'test_id': str(test['_id'])}):
        true_value_idx = model.labels.index(example['label'])

        prob0, prob1 = example['prob'][:2]
        weighted_sum = weight1 * prob0 + weight0 * prob1
        weighted_prob0 = weight1 * prob0 / weighted_sum
        weighted_prob1 = weight0 * prob1 / weighted_sum

        predicted = [weighted_prob0, weighted_prob1].index(max([weighted_prob0, weighted_prob1]))
        matrix[true_value_idx][predicted] += 1

    return matrix


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
            for example in test.get_examples_full_data(None):
                rows = []
                for field in fields:
                    val = example[field] if field in example else ''
                    rows.append(val)
                writer.writerow(rows)
        return filename

    init_logger('get_csv_results_log', obj=test_id)

    test = app.db.Test.find_one({
        'model_id': model_id,
        '_id': ObjectId(test_id)
    })
    if not test:
        logging.error('Test not found')
        return None

    name = 'Examples-{0!s}.csv'.format(uuid.uuid1())
    expires = 60 * 60 * 24 * 7  # 7 days
    test.exports.append({
        'name': name,
        'fields': fields,
        'status': Test.EXPORT_STATUS_IN_PROGRESS,
        'datetime': datetime.now(),
        'url': None,
        'type': 'csv',
        'expires': datetime.now() + timedelta(seconds=expires)
    })
    test.save()

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

    export = next((ex for ex in test.exports if ex['name'] == name))
    export['url'] = url
    export['status'] = Test.EXPORT_STATUS_COMPLETED
    export['expires'] = datetime.now() + timedelta(seconds=expires)
    test.save()

    return url


def decode(row):
    from decimal import Decimal
    for key, val in row.iteritems():
        try:
            if isinstance(val, basestring):
                row[key] = val.encode('ascii', 'ignore')
            if isinstance(val, Decimal):
                row[key] = val.to_eng_string()
        except UnicodeDecodeError:
            #logging.error('Error while decoding %s: %s', val, exc)
            row[key] = ""
    return row
