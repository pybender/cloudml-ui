import logging
import numpy as np
from api.amazon_utils import AmazonS3Helper
from os.path import exists
from os import makedirs
from datetime import datetime
import numpy
import tempfile

from core.trainer.trainer import Trainer
from core.trainer.config import FeatureModel

from api import celery, app
from api.base.models import db
from api.base.tasks import SqlAlchemyTask
from api.base.exceptions import InvalidOperationError
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model, Weight, WeightsCategory, Segment, \
    Transformer, get_transformer, ClassifierGridParams
from api.model_tests.models import TestResult, TestExample
from api.import_handlers.models import DataSet
from api.logs.dynamodb.models import LogMessage
from api.servers.models import Server

db_session = db.session


@celery.task(base=SqlAlchemyTask)
def train_model(dataset_ids, model_id, user_id, delete_metadata=False):
    """
    Train new model celery task.
    """
    init_logger('trainmodel_log', obj=int(model_id))
    logging.info('Start training task')

    user = User.query.get(user_id)
    model = Model.query.get(model_id)
    datasets = DataSet.query.filter(DataSet.id.in_(dataset_ids)).all()
    logging.info('Model: %s' % model.name)
    try:
        model.comparable = False
        model.datasets = datasets
        model.status = model.STATUS_TRAINING
        model.error = ""
        model.trained_by = user
        model.save(commit=True)

        if delete_metadata:
            logging.info('Remove old model data on retrain model')
            LogMessage.delete_related_logs(model.id)  # rem logs from mongo
            count = TestExample.query.filter(
                TestExample.model_id == model.id).delete(
                    synchronize_session=False)
            logging.info('%s tests examples to delete' % count)
            count = TestResult.query.filter(
                TestResult.model_id == model.id).delete(
                    synchronize_session=False)
            logging.info('%s tests to delete' % count)
            db_session.commit()

            count = Weight.query.filter(
                Weight.model_id == model.id).delete(
                    synchronize_session=False)
            logging.info('%s weights to delete' % count)
            db_session.commit()

            count = WeightsCategory.query.filter(
                WeightsCategory.model_id == model.id).delete(
                    synchronize_session=False)
            logging.info('%s weight categories to delete' % count)

            count = Segment.query.filter(
                Segment.model_id == model_id).delete(
                    synchronize_session=False)
            logging.info('%s segments to delete' % count)
            db_session.commit()

        logging.info('Perform model training')
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
        train_begin_time = datetime.utcnow()

        trainer.set_transformer_getter(get_transformer)
        trainer.train(train_iter)

        mem_usage = memory_usage(-1, interval=0, timeout=None)
        trainer.clear_temp_data()

        model.set_trainer(trainer)
        model.save()
        model.memory_usage = max(mem_usage)
        model.train_records_count = int(sum((
            d.records_count for d in model.datasets)))
        train_end_time = datetime.utcnow()
        model.training_time = int((train_end_time - train_begin_time).seconds)
        model.save()

        model.create_segments(trainer._get_segments_info())

        for segment in model.segments:
            fill_model_parameter_weights.delay(model.id, segment.id)

    except Exception, exc:
        db_session.rollback()

        logging.exception('Got exception when train model')
        model.status = model.STATUS_ERROR
        model.error = str(exc)[:299]
        model.save()
        raise

    msg = "Model trained at %s" % trainer.train_time
    logging.info(msg)
    return msg


@celery.task(base=SqlAlchemyTask)
def get_classifier_parameters_grid(grid_params_id):
    grid_params = ClassifierGridParams.query.get(grid_params_id)
    grid_params.status = 'Calculating'
    grid_params.save()
    feature_model = FeatureModel(
        grid_params.model.get_features_json(), is_file=False)
    trainer = Trainer(feature_model)

    def _get_iter(dataset):
        fp = None
        if fp:
            fp.close()
        fp = dataset.get_data_stream()
        for row in dataset.get_iterator(fp):
            yield row
        if fp:
            fp.close()

    clfs = trainer.grid_search(
        grid_params.parameters,
        _get_iter(grid_params.train_dataset),
        _get_iter(grid_params.test_dataset),
        score='accuracy')
    grids = {}
    for segment, clf in clfs.iteritems():
        grids[segment] = [{
            'parameters': item.parameters,
            'mean': item.mean_validation_score,
            'std': np.std(item.cv_validation_scores)}
            for item in clf.grid_scores_]
    grid_params.parameters_grid = grids
    grid_params.status = 'Completed'
    grid_params.save()
    return "grid_params done"


@celery.task(base=SqlAlchemyTask)
def fill_model_parameter_weights(model_id, segment_id=None):
    # from core.trainer.classifier_settings import CLASSIFIER_WITH_COEF
    init_logger('trainmodel_log', obj=int(model_id))
    model, segment = _get_model_and_segment_or_raise(model_id, segment_id)
    logging.info("Starting to visualize trained model. Segment: %s" % segment.name)
    trainer = model.get_trainer()

    # need to sync model weights
    count = len(segment.weights)
    if count > 0:
        raise InvalidOperationError(
            'Weights for model %s already filled: %s' %
            (model_id, count))

    weights_dict = None

    def process_weights_for_class(class_label):
        """
        Adds weights for specific class, also adds new categories not found
        in `categories_names`
        :param class_label: class_label of the weights to process
        :return:
        """
        w_added = 0
        cat_added = 0
        weights = weights_dict[class_label]
        logging.info("Model: %s , Segment: %s, Class: %s" %
                     (model.name, segment.name, class_label))

        positive = weights['positive']
        negative = weights['negative']

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

        from collections import defaultdict
        tree = defaultdict(dict)
        tree['weights'] = []
        categories_names = []

        # Adding weights and weights categories to db
        for weight in weight_list:
            name = weight['name']
            splitted_name = name.split('->')
            long_name = ''
            count = len(splitted_name)
            current = tree
            for i, sname in enumerate(splitted_name):
                parent = long_name
                long_name = '%s.%s' % (long_name, sname) \
                    if long_name else sname
                if i == (count - 1):
                    # The leaf of the split (last element) is not a category,
                    # it is the actual weight
                    new_weight = Weight()
                    new_weight.name = weight['name']
                    new_weight.value = weight['weight']
                    new_weight.value2 = weight['feature_weight']
                    new_weight.is_positive = bool(weight['weight'] > 0)
                    new_weight.css_class = weight['css_class']
                    new_weight.parent = parent
                    new_weight.short_name = sname[0:199]
                    new_weight.model_name = model.name
                    new_weight.model = model
                    new_weight.segment = segment
                    new_weight.class_label = str(class_label)
                    new_weight.save(commit=False)
                    w_added += 1

                    current['weights'].append(new_weight)
                else:
                    # Intermediate elements of the split, are actual categories
                    # except of the last one (which is the actual weight)
                    if long_name not in categories_names:
                        # Adding a category, if it has not already added
                        categories_names.append(long_name)
                        category = WeightsCategory()
                        category.name = long_name
                        category.parent = parent
                        category.short_name = sname
                        category.model_name = model.name
                        category.model = model
                        category.segment = segment
                        category.class_label = str(class_label)
                        category.save(commit=False)
                        cat_added += 1
                        current['subcategories'][sname] = {
                            'category': category,
                            'weights': [],
                            'subcategories': {}}
                    current = current['subcategories'][sname]

        # Calculating categories normalized weight
        def calc_tree_item(tree_item, parent=None):
            for category_name, item in tree_item.iteritems():
                if 'category' in item:
                    category = item['category']
                    normalized_weight = 0
                    for w in item['weights']:
                        normalized_weight += w.value2
                        w.category = category
                    category.normalized_weight = normalized_weight
                    if parent:
                        parent.normalized_weight += normalized_weight
                    if 'subcategories' in item:
                        calc_tree_item(item['subcategories'], category)

        calc_tree_item(tree['subcategories'])
        return cat_added, w_added

    model.status = model.STATUS_FILLING_WEIGHTS
    model.save()

    try:
        visualization_data = trainer.get_visualization(segment.name)
        have_weights = 'weights' in visualization_data
        if have_weights:
            weights_dict = visualization_data.pop('weights')
            model.visualization_data = visualization_data

            weights_added = 0
            categories_added = 0
            classes_processed = 0

            for clazz in weights_dict.keys():
                c, w = process_weights_for_class(clazz)
                categories_added += c
                weights_added += w
                classes_processed += 1

            db.session.commit()
            msg = 'Model %s parameters weights was added to db. %s weights, ' \
                  'in %s categories for %s classes' % \
                  (model.name, weights_added, categories_added, classes_processed)
            logging.info(msg)
        else:
            msg = 'Weights are unavailable for the classifier'
            logging.info(msg)

        # TODO:
        if not model.labels:
            model.labels = trainer._get_labels()
        model.status = model.STATUS_TRAINED
        model.weights_synchronized = have_weights
        model.save()

    except Exception, exc:
        logging.exception('Got exception when fill_model_parameter: %s', exc)
        raise
    return msg


def add_weights_to_db(model, segment, class_label, weight_list):
    w_added = 0
    cat_added = 0
    from collections import defaultdict
    tree = defaultdict(dict)
    tree['weights'] = []
    categories_names = []

    # Adding weights and weights categories to db
    for weight in weight_list:
        name = weight['name']
        splitted_name = name.split('->')
        long_name = ''
        count = len(splitted_name)
        current = tree
        for i, sname in enumerate(splitted_name):
            parent = long_name
            long_name = '%s.%s' % (long_name, sname) \
                if long_name else sname
            if i == (count - 1):
                # The leaf of the split (last element) is not a category,
                # it is the actual weight
                new_weight = Weight()
                new_weight.name = weight.get('name')
                new_weight.value = weight.get('weight')
                new_weight.value2 = weight.get('feature_weight') or weight.get('weight')
                new_weight.is_positive = bool(weight.get('weight') > 0)
                new_weight.css_class = weight.get('css_class')
                new_weight.parent = parent
                new_weight.short_name = sname[0:199]
                new_weight.model_name = model.name
                new_weight.model = model
                new_weight.segment = segment
                new_weight.class_label = str(class_label)
                new_weight.save(commit=False)
                w_added += 1

                current['weights'].append(new_weight)
            else:
                # Intermediate elements of the split, are actual categories
                # except of the last one (which is the actual weight)
                if long_name not in categories_names:
                    # Adding a category, if it has not already added
                    categories_names.append(long_name)
                    category = WeightsCategory()
                    category.name = long_name
                    category.parent = parent
                    category.short_name = sname
                    category.model_name = model.name
                    category.model = model
                    category.segment = segment
                    category.class_label = str(class_label)
                    category.save(commit=False)
                    cat_added += 1
                    current['subcategories'][sname] = {
                        'category': category,
                        'weights': [],
                        'subcategories': {}}
                current = current['subcategories'][sname]

    # Calculating categories normalized weight
    def calc_tree_item(tree_item, parent=None):
        for category_name, item in tree_item.iteritems():
            if 'category' in item:
                category = item['category']
                normalized_weight = 0
                for w in item['weights']:
                    normalized_weight += w.value2
                    w.category = category
                category.normalized_weight = normalized_weight
                if parent:
                    parent.normalized_weight += normalized_weight
                if 'subcategories' in item:
                    calc_tree_item(item['subcategories'], category)

    calc_tree_item(tree['subcategories'])
    return cat_added, w_added


def _get_model_and_segment_or_raise(model_id, segment_id):
    model = Model.query.get(model_id)
    if model is None:
        raise ValueError('Model not found: %s' % model_id)

    if segment_id is None:
        segment = Segment.query.filter_by(model=model).first()
    else:
        segment = Segment.query.get(segment_id)
    if segment is None:
        raise ValueError('Segment not found: %s' % segment_id)
    return model, segment


@celery.task(base=SqlAlchemyTask)
def transform_dataset_for_download(model_id, dataset_id):
    model = Model.query.get(model_id)
    dataset = DataSet.query.get(dataset_id)

    init_logger('transform_for_download_log', obj=int(dataset_id))
    logging.info('Starting Transform For Download Task')

    transformed = model.transform_dataset(dataset)

    logging.info('Saving transformed data to disk')
    temp_file = tempfile.NamedTemporaryFile()
    numpy.savez_compressed(temp_file, **transformed)

    s3_filename = "dataset_{0}_vectorized_for_model_{1}.npz".format(
        dataset.id, model.id)

    s3 = AmazonS3Helper()
    logging.info('Uploading file {0} to s3 with name {1}...'.format(
        temp_file.name, s3_filename))
    s3.save_key(s3_filename, temp_file.name, {
        'model_id': model.id,
        'dataset_id': dataset.id}, compressed=False)
    s3.close()
    return s3.get_download_url(s3_filename, 60 * 60 * 24 * 7)


@celery.task(base=SqlAlchemyTask)
def train_transformer(dataset_ids, transformer_id, user_id,
                      delete_metadata=False):
    """
    Train the transformer celery task.
    """
    init_logger('traintransformer_log', obj=int(transformer_id))
    logging.info('Start training transformer task')

    user = User.query.get(user_id)
    transformer = Transformer.query.get(transformer_id)
    datasets = DataSet.query.filter(DataSet.id.in_(dataset_ids)).all()
    logging.info('Transformer: %s' % transformer.name)

    try:
        transformer.datasets = datasets
        transformer.status = transformer.STATUS_TRAINING
        transformer.error = ""
        transformer.trained_by = user
        transformer.save(commit=True)

        # TODO: what about models that use this transformer?
        if delete_metadata:
            logging.info('Remove logs on retrain transformer')
            LogMessage.delete_related_logs(transformer.id)

        logging.info('Perform transformer training')
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)

        trainer = {}

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
        train_begin_time = datetime.utcnow()
        trainer = transformer.train(train_iter)

        mem_usage = memory_usage(-1, interval=0, timeout=None)
        #trainer.clear_temp_data()

        transformer.status = transformer.STATUS_TRAINED
        transformer.set_trainer(trainer)
        transformer.save()
        transformer.memory_usage = max(mem_usage)
        transformer.train_records_count = int(sum((
            d.records_count for d in transformer.datasets)))
        train_end_time = datetime.utcnow()
        transformer.training_time = int(
            (train_end_time - train_begin_time).seconds)
        transformer.save()
    except Exception, exc:
        db_session.rollback()

        logging.exception('Got exception when train transformer')
        transformer.status = transformer.STATUS_ERROR
        transformer.error = str(exc)[:299]
        transformer.save()
        raise

    msg = "Transformer trained"
    logging.info(msg)
    return msg
