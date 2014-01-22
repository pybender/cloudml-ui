import logging
import os
import csv
import json
from datetime import datetime

from api.logs.logger import init_logger
from api import celery
from api.ml_models.models import Model
from api.model_tests.models import TestResult
from api.base.tasks import SqlAlchemyTask
from models import DataSet


@celery.task(base=SqlAlchemyTask)
def import_data(dataset_id, model_id=None, test_id=None):
    """
    Import data from database.
    """
    from core.importhandler.importhandler import ExtractionPlan, ImportHandler
    try:
        dataset = DataSet.query.get(dataset_id)
        importhandler = dataset.import_handler
        if dataset is None or importhandler is None:
            raise ValueError('DataSet or Import Handler not found')
        obj = None
        if not model_id is None:
            obj = Model.query.get(model_id)
        if not test_id is None:
            obj = TestResult.query.get(test_id)

        if obj:
            obj.status = obj.STATUS_IMPORTING
            obj.save()
        init_logger('importdata_log', obj=dataset.id)
        logging.info('Loading dataset %s' % dataset.id)

        import_start_time = datetime.now()

        logging.info("Import dataset using import handler '%s' \
with%s compression", importhandler.name, '' if dataset.compress else 'out')
        handler = json.dumps(importhandler.data)
        plan = ExtractionPlan(handler, is_file=False)
        handler = ImportHandler(plan, dataset.import_params)
        logging.info('The dataset will be stored to file %s', dataset.filename)

        if dataset.format == dataset.FORMAT_CSV:
            handler.store_data_csv(dataset.filename, dataset.compress)
        else:
            handler.store_data_json(dataset.filename, dataset.compress)

        logging.info('Import dataset completed')

        logging.info('Retrieving data fields')
        with dataset.get_data_stream() as fp:
            if dataset.format == dataset.FORMAT_CSV:
                reader = csv.DictReader(
                    fp,
                    quotechar="'",
                    quoting=csv.QUOTE_ALL
                )
                row = next(reader)
            else:
                row = next(fp)
                if row:
                    row = json.loads(row)
            if row:
                dataset.data_fields = row.keys()

        logging.info('Dataset fields: {0!s}'.format(dataset.data_fields))

        dataset.filesize = long(os.path.getsize(dataset.filename))
        dataset.records_count = handler.count
        dataset.status = dataset.STATUS_UPLOADING
        dataset.save()

        logging.info('Saving file to Amazon S3')
        dataset.save_to_s3()
        logging.info('File saved to Amazon S3')
        dataset.time = (datetime.now() - import_start_time).seconds

        dataset.status = dataset.STATUS_IMPORTED
        if obj:
            obj.status = obj.STATUS_IMPORTED
            obj.save()

        dataset.save()

        logging.info('DataSet was loaded')
    except Exception, exc:
        logging.exception('Got exception when import dataset')
        dataset.set_error(exc)
        if obj:
            obj.set_error(exc)
        raise

    logging.info("Dataset using %s imported.", importhandler.name)
    return [dataset_id]


@celery.task(base=SqlAlchemyTask)
def upload_dataset(dataset_id):
    """
    Upload dataset to S3.
    """
    dataset = DataSet.query.get(dataset_id)
    try:
        if not dataset:
            raise ValueError('DataSet not found')
        init_logger('importdata_log', obj=dataset.id)
        logging.info('Uploading dataset %s' % dataset.id)

        dataset.status = dataset.STATUS_UPLOADING
        dataset.save()

        logging.info('Saving file to Amazon S3')
        dataset.save_to_s3()
        logging.info('File saved to Amazon S3')

        dataset.status = dataset.STATUS_IMPORTED
        if dataset.records_count is None:
            dataset.records_count = 0
        dataset.save()

    except Exception, exc:
        logging.exception('Got exception when uploading dataset')
        dataset.set_error(exc)
        raise

    logging.info("Dataset using {0!s} uploaded.".format(dataset))
    return [dataset_id]
