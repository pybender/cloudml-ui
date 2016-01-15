"""
Model specific celery tasks.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import numpy
import tempfile
import numpy as np
from datetime import datetime

from cloudml.trainer.trainer import Trainer, DEFAULT_SEGMENT
from cloudml.trainer.config import FeatureModel

from api import celery, app
from api.base.tasks import SqlAlchemyTask, TaskException, get_task_traceback
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model, Segment
from api.import_handlers.models import DataSet
from api.logs.dynamodb.models import LogMessage
from api.base.io_utils import get_or_create_data_folder
from api.base.resources.exceptions import NotFound


__all__ = ['train_model', 'get_classifier_parameters_grid',
           'visualize_model', 'generate_visualization_tree',
           'transform_dataset_for_download']


@celery.task(base=SqlAlchemyTask)
def train_model(dataset_ids, model_id, user_id, delete_metadata=False):
    """
    Train or re-train the model.

    dataset_ids: list of integers
        List of dataset ids used for model training.
    model_id: int
        Id of the model to train.
    user_id: int
        Id of the user, who initiate training the model.
    delete_metadata: bool
        Whether we need model related db logs, test results and
        other model related data.
    """
    init_logger('trainmodel_log', obj=int(model_id))
    logging.info('Start training task')

    user = User.query.get(user_id)
    model = Model.query.get(model_id)
    datasets = DataSet.query.filter(DataSet.id.in_(dataset_ids)).all()
    logging.info('Preparing the model `%s` for training.' % model.name)
    try:
        model.prepare_fields_for_train(user=user, datasets=datasets)
        logging.info(
            'DataSet files chosen for training: %s'
            % ', '.join(['{0} (id #{1})'
                        .format(dataset.filename, dataset.id) for dataset
                         in datasets]))
        logging.info('Perform model training')
        feature_model = FeatureModel(model.get_features_json(),
                                     is_file=False)
        trainer = Trainer(feature_model)
        get_or_create_data_folder()

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
        # mem_usage = memory_usage((trainer.train,
        #                          (train_iter,)), interval=0)
        train_begin_time = datetime.utcnow()

        from api.ml_models.models import get_transformer
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

        segments = trainer._get_segments_info()
        if not segments or not segments.keys():
            raise Exception('No segments in the model')

        model.create_segments(segments)

        for segment in model.segments:
            visualize_model.delay(model.id, segment.id)

    except Exception, exc:
        app.sql_db.session.rollback()

        logging.error(
            'Got exception when train model: {0!s} \n {1}'
            .format(exc, get_task_traceback(exc)))
        model.status = model.STATUS_ERROR
        model.error = str(exc)[:299]
        model.save()
        raise TaskException(exc.message, exc)

    msg = "Model trained at %s" % trainer.train_time
    logging.info(msg)
    return msg


@celery.task(base=SqlAlchemyTask)
def get_classifier_parameters_grid(grid_params_id):
    """
    Exhaustive search over specified parameter values for an estimator.
    Fills parameters_grid field of the ClassifierGridParams object with
    grid search result.

    grid_params_id: int
        ID of the ClassifierGridParams model, that contains link to the
        model, datasets for training and testing, parameters, choosen by
        user.
    """
    from api.ml_models.models import ClassifierGridParams
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
        score=grid_params.scoring)
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
def visualize_model(model_id, segment_id=None):
    """
    Generates Trained model visualization. Fills weights and creates weights
    tree.

    model_id: int
        Id of the model.
    segment_id: int
        ID of the model segment.
    """
    init_logger('trainmodel_log', obj=int(model_id))
    model, segment = _get_model_and_segment_or_raise(model_id, segment_id)

    logging.info(
        "Starting to visualize trained model {0}. Segment: {1}".format(
            model.name, segment.name))
    trainer = model.get_trainer()

    # need to sync model weights
    count = len(segment.weights)
    if count > 0:
        from api.base.exceptions import InvalidOperationError
        raise InvalidOperationError(
            'Weights for model %s already filled: %s' % (model_id, count))

    weights_dict = None
    model.status = model.STATUS_FILLING_WEIGHTS
    model.save()

    try:
        visualization_data = trainer.get_visualization(segment.name)
        have_weights = 'weights' in visualization_data
        if have_weights:
            from utils import fill_model_weights
            weights_dict = visualization_data.pop('weights')
            weights_added = 0
            categories_added = 0
            classes_processed = 0

            for clazz in weights_dict.keys():
                c, w = fill_model_weights(
                    model, segment, clazz, weights_dict[clazz])
                categories_added += c
                weights_added += w
                classes_processed += 1

            app.sql_db.session.commit()
            logging.info(
                'Model %s parameters weights was added to db. %s weights, '
                'in %s categories for %s classes' %
                (model.name, weights_added, categories_added,
                 classes_processed))
        else:
            logging.info('Weights are unavailable for the classifier')

        # TODO:
        if not model.labels:
            model.labels = trainer._get_labels()
        model.visualize_model(segment=segment.name, data=visualization_data,
                              commit=False)
        model.status = model.STATUS_TRAINED
        model.weights_synchronized = have_weights
        model.save()

    except Exception, exc:
        logging.error('Got exception when visualize the model: {0} \n {1}'
                      .format(exc.message, get_task_traceback(exc)))
        raise TaskException(exc.message, exc)
    return 'Segment %s of the model %s has been visualized' % \
        (segment.name, model.name)


@celery.task(base=SqlAlchemyTask)
def generate_visualization_tree(model_id, deep):
    """
    Generates Visualization tree with specified `deep`.

    Parameters
    ----------
    model_id: integer
        Database id of the model

    deep : positive integer
        Maximum tree deep.

    Notes
    -----
    Decision Tree Classifier and Random Forest Classifier are supported.
    """
    from cloudml.trainer.classifier_settings import DECISION_TREE_CLASSIFIER, \
        RANDOM_FOREST_CLASSIFIER, EXTRA_TREES_CLASSIFIER
    from exceptions import VisualizationException

    init_logger('trainmodel_log', obj=int(model_id))
    logging.info('Starting tree visualization')
    model = Model.query.get(model_id)

    if model is None:
        raise NotFound('model not found: %s' % model_id)

    if model.classifier is None or 'type' not in model.classifier:
        raise ValueError('model has invalid classifier')

    clf_type = model.classifier['type']
    if clf_type not in (DECISION_TREE_CLASSIFIER,
                        RANDOM_FOREST_CLASSIFIER,
                        EXTRA_TREES_CLASSIFIER):
        raise VisualizationException(
            "model with %s classifier doesn't support tree"
            " visualization" % clf_type,
            VisualizationException.CLASSIFIER_NOT_SUPPORTED)

    # Checking that all_weights had been stored while training model
    # For old models we need to retrain the model.
    if model.visualization_data is None:
        raise VisualizationException(
            "we don't support the visualization re-generation for "
            "models trained before may 2015."
            "please re-train the model to use this feature.",
            error_code=VisualizationException.ALL_WEIGHT_NOT_FILLED)

    trainer = model.get_trainer()
    from copy import deepcopy
    data = deepcopy(model.visualization_data)
    segments = [segment.name for segment in model.segments] \
        or [DEFAULT_SEGMENT]
    for segment in segments:
        if segment not in model.visualization_data \
                or 'all_weights' not in model.visualization_data[segment]:
            raise VisualizationException(
                "we don't support the visualization re-generation for models"
                " trained before may 2015."
                "please re-train the model to use this feature.",
                error_code=VisualizationException.ALL_WEIGHT_NOT_FILLED)

        if clf_type == DECISION_TREE_CLASSIFIER:
            tree = trainer.model_visualizer.regenerate_tree(
                segment, data[segment]['all_weights'], deep=deep)
            data[segment]['tree'] = tree
        elif clf_type == RANDOM_FOREST_CLASSIFIER or \
                clf_type == EXTRA_TREES_CLASSIFIER:
            trees = trainer.model_visualizer.regenerate_trees(
                segment, data[segment]['all_weights'], deep=deep)
            data[segment]['trees'] = trees
        data[segment]['parameters'] = {'deep': deep, 'status': 'done'}

    model.visualize_model(data)
    return "Tree visualization was completed"


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

    from api.amazon_utils import AmazonS3Helper
    s3 = AmazonS3Helper()
    logging.info('Uploading file {0} to s3 with name {1}...'.format(
        temp_file.name, s3_filename))
    s3.save_key(s3_filename, temp_file.name, {
        'model_id': model.id,
        'dataset_id': dataset.id}, compressed=False)
    s3.close()
    return s3.get_download_url(s3_filename, 60 * 60 * 24 * 7)


def _get_model_and_segment_or_raise(model_id, segment_id=None):
    model = Model.query.get(model_id)
    if model is None:
        raise NotFound('Model not found: %s' % model_id)

    if segment_id is None:
        segment = Segment.query.filter_by(model=model).first()
    else:
        segment = Segment.query.get(segment_id)
    if segment is None:
        raise NotFound('Segment not found: %s' % segment_id)
    return model, segment
