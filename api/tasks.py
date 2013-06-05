import json
import logging
from copy import copy
from itertools import izip
from bson.objectid import ObjectId
from os.path import join, exists
from os import makedirs

from api import celery, app
from api.models import Test
from api.logger import init_logger
from core.trainer.trainer import Trainer
from core.trainer.config import FeatureModel
from core.trainer.streamutils import streamingiterload


class InvalidOperationError(Exception):
    pass


@celery.task
def import_data(dataset_id):
    """
    Import data from database.
    """
    from core.importhandler.importhandler import ExtractionPlan, ImportHandler
    init_logger('importdata_log', dataset_id=dataset_id)
    try:
        dataset = app.db.DataSet.find_one({'_id': ObjectId(dataset_id)})
        importhandler = app.db.ImportHandler.find_one(
            {'_id': ObjectId(dataset.import_handler_id)})
        handler = json.dumps(importhandler.data)
        plan = ExtractionPlan(handler, is_file=False)
        handler = ImportHandler(plan, dataset.import_params)

        logging.info("Loading data using %s imported.", importhandler.name)
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        handler.store_data_json(join(path, dataset.data))
        dataset.status = dataset.STATUS_IMPORTED
        dataset.save(validate=True)
    except Exception, exc:
        logging.error(exc)
        dataset.set_error(exc)
        raise

    logging.info("Dataset using %s imported.", importhandler.name)
    return dataset_id


@celery.task
def train_model(dataset_id, model_id):
    """
    Train new model celery task.
    """
    init_logger('trainmodel_log', model=model_id)

    try:
        model = app.db.Model.find_one({'_id': ObjectId(model_id)})
        dataset = app.db.DataSet.find_one({'_id': ObjectId(dataset_id)})
        model.delete_metadata()

        model.status = model.STATUS_TRAINING
        model.error = ""
        model.save(validate=True)
        feature_model = FeatureModel(json.dumps(model.features),
                                     is_file=False)
        trainer = Trainer(feature_model)
        with open(dataset.data, 'r') as train_fp:
            trainer.train(streamingiterload(train_fp))
        trainer.clear_temp_data()
        model.status = model.STATUS_TRAINED
        model.set_trainer(trainer)
        model.save()
        fill_model_parameter_weights.delay(str(model._id))
    except Exception, exc:
        logging.error(exc)
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
    logging.info("Starting to fill model weights")
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
    positive_weights = calc_weights_css(positive, 'green')
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
                weight.save(validate=True, check_keys=False, safe=False)
            else:
                if sname not in category_names:
                    # Adding a category, if it has not already added
                    category_names.append(sname)
                    params.update({'name': long_name})
                    category = app.db.WeightsCategory(params)
                    category.save(validate=True, check_keys=False, safe=False)

    model.weights_synchronized = True
    model.save()
    msg = 'Model %s parameters weights was added to db: %s' % \
        (model.name, len(weight_list))
    logging.info(msg)
    return msg


@celery.task
def run_test(test_id):
    """
    Running tests for trained model
    """
    init_logger('runtest_log', test=test_id)

    test = app.db.Test.find_one({'_id': ObjectId(test_id)})
    model = test.model
    try:
        if model.status != model.STATUS_TRAINED:
            raise InvalidOperationError("Train the model before")

        test.status = test.STATUS_IN_PROGRESS
        test.error = ""
        test.save()

        parameters = copy(test.parameters)
        metrics, raw_data = model.run_test(parameters)
        test.accuracy = metrics.accuracy

        metrics_dict = metrics.get_metrics_dict()

        # TODO: Refactor this. Here are possible issues with conformity
        # between labels and values
        confusion_matrix = metrics_dict['confusion_matrix']
        confusion_matrix_ex = []
        for i, val in enumerate(metrics.classes_set):
            confusion_matrix_ex.append((str(val), confusion_matrix[i]))
        metrics_dict['confusion_matrix'] = confusion_matrix_ex
        n = len(raw_data) / 100 or 1
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
        test.save()

        def store_examples(items):
            count = 0
            for row, label, pred, prob in items:
                count += 1
                if count % 100 == 0:
                    logging.info('Stored %d rows' % count)
                row = decode(row)
                new_row = {}
                for key, val in row.iteritems():
                    new_key = key.replace('.', '->')
                    new_row[new_key] = val

                example = app.db.TestExample()
                example['data_input'] = new_row
                example['id'] = str(row.get(model.example_id, '-1'))
                example['name'] = str(row.get(model.example_label, 'noname'))
                example['label'] = str(label)
                example['pred_label'] = str(pred)
                example['prob'] = prob.tolist()
                example['test_name'] = test.name
                example['model_name'] = model.name
                example['test_id'] = str(test._id)
                example['model_id'] = str(model._id)
                try:
                    example.validate()
                except Exception, exc:
                    logging.error('Problem with saving example #%s: %s',
                                  count, exc)
                    continue
                example.save(check_keys=False)

        examples = izip(raw_data,
                        metrics._labels,
                        metrics._preds,
                        metrics._probs)
        store_examples(examples)

    except Exception, exc:
        logging.error(exc)
        test.status = test.STATUS_ERROR
        test.error = str(exc)
        test.save()
        raise
    return 'Test completed'


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
