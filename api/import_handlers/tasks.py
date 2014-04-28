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
from api.instances.models import Cluster
from models import DataSet


@celery.task(base=SqlAlchemyTask)
def import_data(dataset_id, model_id=None, test_id=None):
    """
    Import data from database.
    """
    def get_parent_object():
        if not model_id is None:
            return Model.query.get(model_id)
        if not test_id is None:
            return TestResult.query.get(test_id)

    def set_error(err, ds=None, parent=None):
        if ds is not None:
            ds.set_error(err)
        if parent is not None:
            parent.set_error(err)

    obj = get_parent_object()
    dataset = DataSet.query.get(dataset_id)
    if dataset is None:
        set_error("Dataset with id %s not found" % dataset_id, parent=obj)

    import_handler = dataset.import_handler
    if import_handler is None:
        set_error("Import handler for dataset %s not found" %
                  dataset_id, ds=dataset, parent=obj)
    if obj:
        obj.status = obj.STATUS_IMPORTING
        obj.save()

    try:
        init_logger('importdata_log', obj=dataset.id)
        logging.info('Loading dataset %s' % dataset.id)

        import_start_time = datetime.now()
        def callback(jobflow_id, master_dns):
            cluster = Cluster.query.filter(Cluster.jobflow_id==jobflow_id).first()
            if cluster is None:
                cluster = Cluster(jobflow_id=jobflow_id, master_node_dns=master_dns)
                cluster.save()
            dataset.cluster = cluster
            dataset.save()
            logging.info('Master dns %s' % master_dns)
            cluster.create_ssh_tunnel()


        logging.info("Import dataset using import handler '%s' \
with%s compression", import_handler.name, '' if dataset.compress else 'out')

        handler_iterator = import_handler.get_iterator(dataset.import_params, callback)

        logging.info('The dataset will be stored to file %s', dataset.filename)

        if dataset.format == dataset.FORMAT_CSV:
            handler_iterator.store_data_csv(
                dataset.filename, dataset.compress)
        else:
            handler_iterator.store_data_json(
                dataset.filename, dataset.compress)

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
        dataset.records_count = handler_iterator.count
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
        set_error(exc, ds=dataset, parent=obj)
        raise

    logging.info("Dataset using %s imported.", import_handler.name)
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
