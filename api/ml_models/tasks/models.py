"""
Model specific celery tasks.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
import numpy
import tempfile
import numpy as np
import datetime
import dateutil.relativedelta
import os
from api.config import DATA_FOLDER

from cloudml.trainer.trainer import Trainer, DEFAULT_SEGMENT
from cloudml.trainer.config import FeatureModel

from api import celery, app
from api.base.tasks import SqlAlchemyTask
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Model, Segment, Transformer
from api.import_handlers.models import DataSet
from api.logs.dynamodb.models import LogMessage
from api.base.io_utils import get_or_create_data_folder


__all__ = ['train_model', 'get_classifier_parameters_grid',
           'visualize_model', 'generate_visualization_tree',
           'transform_dataset_for_download',
           'upload_segment_features_transformers', 'clear_model_data_cache']


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
            % ', '.join(['{0} (id #{1})'.
                        format(dataset.filename, dataset.id)
                         for dataset in datasets]))
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
        train_begin_time = datetime.datetime.utcnow()

        from api.ml_models.models import get_transformer
        trainer.set_transformer_getter(get_transformer)
        trainer.train(train_iter)

        mem_usage = memory_usage(-1, interval=0, timeout=None)
        trainer.clear_temp_data()

        logging.info('Store trainer to s3')
        model.set_trainer(trainer)
        model.save()
        logging.info('Set train records')
        model.memory_usage = max(mem_usage)
        model.train_records_count = int(sum((
            d.records_count for d in model.datasets)))
        train_end_time = datetime.datetime.utcnow()
        model.training_time = int((train_end_time - train_begin_time).seconds)
        model.save()
        logging.info('Get segment info')
        segments = trainer._get_segments_info()
        if not segments or not segments.keys():
            raise Exception('No segments in the model')

        model.create_segments(segments)

        for segment in model.segments:
            visualize_model.delay(model.id, segment.id)

    except Exception, exc:
        app.sql_db.session.rollback()

        try:
            logging.exception(
                'Got exception when train model: {0!s}'.format(exc))
        except:
            logging.error('Got exception when train model: {0!s}'.format(exc))
        model.status = model.STATUS_ERROR
        model.error = str(exc)[:299]
        model.save()
        raise

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
    init_logger('gridsearch_log', obj=int(grid_params_id))
    logging.info('Parameters grid search task started')

    from api.ml_models.models import ClassifierGridParams
    grid_params = ClassifierGridParams.query.get(grid_params_id)
    grid_params.status = 'Calculating'
    grid_params.save()
    try:
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
    except Exception, e:
        logging.exception('Got exception on grid params search: {}'.format(e))
        grid_params.status = 'Error'
        grid_params.save()
        raise

    msg = "Parameters grid search done"
    logging.info(msg)
    return msg


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
        from cloudml.trainer.classifier_settings import CLASSIFIER_MODELS
        clf_type = model.classifier.get('type')
        if clf_type in CLASSIFIER_MODELS and not model.labels:
            model.labels = trainer._get_labels()
        model.visualize_model(segment=segment.name, data=visualization_data,
                              commit=False)
        model.status = model.STATUS_TRAINED
        model.weights_synchronized = have_weights
        model.save()

    except Exception, exc:
        logging.exception('Got exception when visualize the model: %s', exc)
        model.status = model.STATUS_ERROR
        model.error = str(exc)[:299]
        model.save()
        raise
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
        raise ValueError('model not found: %s' % model_id)

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
        raise ValueError('Model not found: %s' % model_id)

    if segment_id is None:
        segment = Segment.query.filter_by(model=model).first()
    else:
        segment = Segment.query.get(segment_id)
    if segment is None:
        raise ValueError('Segment not found: %s' % segment_id)
    return model, segment


@celery.task(base=SqlAlchemyTask)
def upload_segment_features_transformers(model_id, segment_id, fformat):
    model = Model.query.get(model_id)
    segment = Segment.query.get(segment_id)
    log_id = segment_id
    from api.async_tasks.models import AsyncTask
    if upload_segment_features_transformers.request.id is not None:
        tasks = AsyncTask.query\
            .filter_by(
                task_id=upload_segment_features_transformers.request.id
            ).limit(1)
        log_id = tasks[0].id

    init_logger('prepare_transformer_for_download_log',
                obj=int(log_id))
    logging.info('Start preparing segment features transformers for download')

    try:
        from zipfile import ZipFile, ZIP_DEFLATED
        from api.amazon_utils import AmazonS3Helper
        import os
        from tempfile import NamedTemporaryFile
        files = []
        arc_name = "{0}-{1}-{2}.zip".format(model.name, segment.name, fformat)

        def _save_content(content, feature_name, transformer_type):
            filename = "{0}-{1}-{2}-data.{3}".format(segment.name,
                                                     feature_name,
                                                     transformer_type,
                                                     fformat)
            logging.info("Creating %s" % filename)
            if fformat == 'csv':
                import csv
                import StringIO
                si = StringIO.StringIO()
                if len(content):
                    fieldnames = content[0].keys()
                    writer = csv.DictWriter(si, fieldnames=fieldnames)
                    writer.writeheader()
                    for c in content:
                        writer.writerow(c)
                response = si.getvalue()
            else:
                import json
                response = json.dumps(content, indent=2)

            with open(filename, 'w') as fh:
                fh.write(response)
                fh.close()
            return filename

        trainer = model.get_trainer()
        if segment.name not in trainer.features:
            raise Exception("Segment %s doesn't exists in trained model" %
                            segment.name)
        for name, feature in trainer.features[segment.name].iteritems():
            if "transformer" in feature and feature["transformer"] is not None:
                try:
                    data = feature["transformer"].load_vocabulary()
                    files.append(_save_content(data, name,
                                               feature["transformer-type"]))
                except AttributeError:
                    logging.warning(
                        "Can't load transformer data for segment {0} feature "
                        "{1} transformer {2}. Transformer doesn't have "
                        "vocabulary to return or feature haven't been "
                        "transformed on model training"
                        .format(segment.name, name,
                                feature["transformer-type"]))
                    continue

        logging.info("Add files to archive")
        with ZipFile(arc_name, "w") as z:
            for f in files:
                z.write(f, compress_type=ZIP_DEFLATED)
            z.close()

        s3 = AmazonS3Helper()
        logging.info('Uploading archive to s3 with name {0}'.format(arc_name))
        s3.save_key(arc_name, arc_name, {
            'model_id': model.id,
            'segment_id': segment_id}, compressed=False)
        s3.close()
        return s3.get_download_url(arc_name, 60 * 60 * 24 * 7)

    except Exception, e:
        logging.exception("Got exception when preparing features transformers "
                          "of segment {0} for download: {1}"
                          .format(segment.name, e.message))
        raise

    finally:
        for f in files:
            os.remove(f)
        if os.path.exists(arc_name):
            os.remove(arc_name)


@celery.task(base=SqlAlchemyTask)
def clear_model_data_cache():
    """Deletes trainer files and datasets from data and test data folders"""
    now = datetime.datetime.now()
    month_ago = now + dateutil.relativedelta.relativedelta(months=-1)
    logging.info("Check and delete files in %s older than %s" % (DATA_FOLDER,
                                                                 month_ago))
    if os.path.exists(DATA_FOLDER):
        files = [f for f in os.listdir(DATA_FOLDER)
                 if os.path.isfile(os.path.join(DATA_FOLDER, f))]
        datasets = []
        models = Model.query.filter(Model.updated_on > month_ago).all()
        model_trainers = ["{}.dat".format(m.get_trainer_filename())
                          for m in models]
        for model in models:
            datasets.extend(model.datasets)
        transformers = Transformer.query\
            .filter(Transformer.updated_on > month_ago).all()
        tf_trainers = ["{}.dat".format(tf.get_trainer_filename())
                       for tf in transformers]
        for tf in transformers:
            datasets.extend(tf.datasets)

        dataset_files = [ds.data for ds in datasets if ds.data]

        for f in files:
            if f not in set(dataset_files) and f not in model_trainers \
                    and f not in tf_trainers:
                os.remove(os.path.join(DATA_FOLDER, f))
                logging.info("{} deleted".format(f))

    try:
        from api.test_config import DATA_FOLDER as TEST_DATA_FOLDER
        logging.info("Clear %s folder ..." % TEST_DATA_FOLDER)
        if os.path.exists(TEST_DATA_FOLDER):
            for f in os.listdir(TEST_DATA_FOLDER):
                fp = os.path.join(TEST_DATA_FOLDER, f)
                if os.path.isfile(fp):
                    os.remove(fp)
    except Exception:
        pass
    logging.info("Finished")
