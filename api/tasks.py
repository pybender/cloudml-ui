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
        fill_model_parameter_weights.delay(model.name, **trainer.get_weights())
        model.save()
    except Exception, exc:
        logging.error(exc)
        model.status = model.STATUS_ERROR
        model.error = str(exc)
        model.save()
        raise

    return "Model trained at %s" % trainer.train_time

from mongotools.pubsub import Channel


class MongoHandler(logging.Handler):
    """
    """
    def __init__(self, test_id):
        super(MongoHandler, self).__init__()
        self.test_id = test_id

    def emit(self, record):
        chan = Channel(app.db, 'log')
        chan.ensure_channel()
        try:
            msg = self.format(record)
            chan.pub('test_log', {'test': self.test_id, 'msg': msg})
        except:
            self.handleError(record)


@celery.task
def fill_model_parameter_weights(model_name, positive, negative):
    """
    Adds model parameters weights to db.
    """
    model = app.db.Model.find_one({'name': model_name})
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
                      'parent': parent,
                      'short_name': sname}
            if i == (count - 1):
                params.update({'name': weight['name'],
                               'value': weight['weight'],
                               'is_positive': bool(weight['weight'] > 0),
                               'css_class': weight['css_class']})
                app.db.Weight.collection.insert(params)
            else:
                if sname not in category_names:
                    # Adding a category, if it has not already added
                    category_names.append(sname)
                    params.update({'name': long_name})
                    app.db.WeightsCategory.collection.insert(params)
    model.weights_synchronized = True
    model.save()
    return 'Model %s parameters weights was added to db: %s' % \
        (model.name, len(weight_list))


@celery.task
def run_test(test_id):
    """
    Running tests for trained model
    """

    logger = logging.getLogger()
    #handler = logging.FileHandler('test-%s.log' % test_id)
    handler = MongoHandler(test_id=test_id)
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = True

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
