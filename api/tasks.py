import json
import logging
from copy import copy
from itertools import izip

from api import celery, app
from bson.objectid import ObjectId

from core.trainer.trainer import Trainer
from core.trainer.config import FeatureModel
from api.models import Test, Model
from helpers.weights import get_weighted_data


class InvalidOperationError(Exception):
    pass


@celery.task
def train_model(model_name, parameters):
    """
    Train new model
    """
    try:
        model = app.db.Model.find_one({'name': model_name})
        if model.status == model.STATUS_TRAINED:
            raise InvalidOperationError("Model already trained")
        model.status = model.STATUS_TRAINING
        model.error = ""
        model.save()
        feature_model = FeatureModel(json.dumps(model.features),
                                     is_file=False)
        trainer = Trainer(feature_model)
        train_handler = model.get_import_handler(parameters)
        trainer.train(train_handler)
        trainer.clear_temp_data()
        model.status = model.STATUS_TRAINED
        model.set_trainer(trainer)
        model.set_weights(**trainer.get_weights())
        model.save()
    except Exception, exc:
        logging.error(exc)
        model.status = model.STATUS_ERROR
        model.error = str(exc)
        model.save()
        raise

    return "Model trained at %s" % trainer.train_time


@celery.task
def run_test(test_id):
    """
    Running tests for trained model
    """
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
                example = app.db.TestExample()
                example['data_input'] = row
                # TODO: Specify Example title column in raw data
                example['name'] = row.get('contractor.dev_profile_title',
                                          'noname')
                example['label'] = str(label)
                example['pred_label'] = str(pred)
                example['prob'] = prob.tolist()
                example['test_name'] = test.name
                example['model_name'] = model.name
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
