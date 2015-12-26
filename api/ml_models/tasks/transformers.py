"""
Pretrained feature transformers related celery tasks.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging
from datetime import datetime

from api import celery, app
from api.base.tasks import SqlAlchemyTask, CloudmlUITaskException, \
    get_task_traceback
from api.logs.logger import init_logger
from api.accounts.models import User
from api.ml_models.models import Transformer
from api.import_handlers.models import DataSet
from api.logs.dynamodb.models import LogMessage


__all__ = ['train_transformer']


@celery.task(base=SqlAlchemyTask)
def train_transformer(dataset_ids, transformer_id, user_id,
                      delete_metadata=False):
    """
    Train the transformer.

    dataset_ids: list of integers
        List of dataset ids used for transformer training.
    transformer_id: int
        Id of the transformer to train.
    user_id: int
        Id of the user, who initiate training the transformer.
    delete_metadata: bool
        Whether we need transformer related db logs.
    """
    init_logger('traintransformer_log', obj=int(transformer_id))

    user = User.query.get(user_id)
    transformer = Transformer.query.get(transformer_id)
    datasets = DataSet.query.filter(DataSet.id.in_(dataset_ids)).all()
    logging.info('Prepare for transformer %s training.' % transformer.name)

    try:
        transformer.datasets = datasets
        transformer.status = transformer.STATUS_TRAINING
        transformer.error = ""
        transformer.trained_by = user
        transformer.save(commit=True)

        if delete_metadata:
            logging.info('Remove logs on retrain transformer')
            LogMessage.delete_related_logs(transformer.id)

        logging.info('Perform transformer training')
        from api.base.io_utils import get_or_create_data_folder
        get_or_create_data_folder()

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
        logging.info(
            'DataSet files chosen for training: %s'
            % ', '.join(['{0} (id #{1})'.
            format(dataset.filename, dataset.id) for dataset in datasets]))
        from memory_profiler import memory_usage
        train_begin_time = datetime.utcnow()
        trainer = transformer.train(train_iter)

        mem_usage = memory_usage(-1, interval=0, timeout=None)
        # trainer.clear_temp_data()

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
        app.sql_db.session.rollback()

        logging.error('Got exception when train transformer',
                      exc_info=get_task_traceback(exc))
        transformer.status = transformer.STATUS_ERROR
        transformer.error = str(exc)[:299]
        transformer.save()
        raise CloudmlUITaskException(exc.message, exc)

    msg = "Transformer trained"
    logging.info(msg)
    return msg
