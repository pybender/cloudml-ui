import logging
from os.path import exists
from os import makedirs
from datetime import datetime
from dateutil import parser, tz

from core.trainer.trainer import Trainer
from core.trainer.config import FeatureModel

from api import celery, app
from api.base.models import db
from api.base.exceptions import InvalidOperationError
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model, Weight, WeightsCategory
from api.import_handlers.models import DataSet


@celery.task
def train_model(dataset_ids, model_id, user_id):
    """
    Train new model celery task.
    """
    init_logger('trainmodel_log', obj=int(model_id))

    user = User.query.get(user_id)
    model = Model.query.get(model_id)
    datasets = DataSet.query.filter(DataSet.id.in_(dataset_ids)).all()

    try:
        model.delete_metadata()

        model.datasets = datasets
        model.status = model.STATUS_TRAINING
        model.error = ""
        model.trained_by = user
        model.save()
        feature_model = FeatureModel(model.get_features_json(),
                                     is_file=False)
        trainer = Trainer(feature_model)
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)

        def _chain_datasets(ds_list):
            fp = None
            for d in ds_list:
                if fp:
                    fp.close()
                fp = d.get_data_stream()
                for row in d.get_iterator(fp):
                    yield row
            if fp:
                fp.close()

        train_iter = _chain_datasets(datasets)

        from memory_profiler import memory_usage
        #mem_usage = memory_usage((trainer.train,
        #                          (train_iter,)), interval=0)
        train_begin_time = datetime.utcnow().replace(tzinfo=tz.tzutc())
        trainer.train(train_iter)

        mem_usage = memory_usage(-1, interval=0, timeout=None)
        trainer.clear_temp_data()
        train_end_time = parser.parse(trainer.train_time)

        model.status = model.STATUS_TRAINED
        model.set_trainer(trainer)
        model.save()
        model.memory_usage = max(mem_usage)
        model.train_records_count = int(sum((
            d.records_count for d in model.datasets)))
        model.training_time = int((train_end_time - train_begin_time).seconds)
        model.save()

        fill_model_parameter_weights.delay(model.id)
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
def fill_model_parameter_weights(model_id):
    """
    Adds model parameters weights to db.
    """
    init_logger('trainmodel_log', obj=int(model_id))
    logging.info("Starting to fill model weights")
    try:
        model = Model.query.get(model_id)
        if model is None:
            raise ValueError('Model not found: %s' % model_id)

        weights = model.get_trainer().get_weights()
        positive = weights['positive']
        negative = weights['negative']
        weights = model.weights
        count = len(weights)
        if count > 0:
            raise InvalidOperationError('Weights for model %s already \
    filled: %s' % (model_id, count))

        from api.ml_models.helpers.weights import calc_weights_css
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
                if i == (count - 1):
                    new_weight = Weight()
                    new_weight.name = weight['name'][0:199]
                    new_weight.value = weight['weight']
                    new_weight.is_positive = bool(weight['weight'] > 0)
                    new_weight.css_class = weight['css_class']
                    new_weight.parent = parent
                    new_weight.short_name = sname[0:199]
                    new_weight.model_name = model.name
                    new_weight.model = model
                    new_weight.save(commit=False)
                else:
                    if sname not in category_names:
                        # Adding a category, if it has not already added
                        category_names.append(sname)
                        category = WeightsCategory()
                        category.name = long_name
                        category.parent = parent
                        category.short_name = sname
                        category.model_name = model.name
                        category.model = model
                        category.save(commit=False)
        db.session.commit()

        model.weights_synchronized = True
        model.save()
        msg = 'Model %s parameters weights was added to db: %s' % \
            (model.name, len(weight_list))
        logging.info(msg)
    except Exception, exc:
        logging.exception('Got exception when fill_model_parameter: %s', exc)
        raise
    return msg
