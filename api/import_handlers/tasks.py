import logging
import os
import csv
import json
from datetime import datetime
import gzip
import re

from api.logs.logger import init_logger
from api import celery
from api.ml_models.models import Model, Transformer
from api.model_tests.models import TestResult
from api.base.tasks import SqlAlchemyTask, get_task_traceback, \
    CloudmlUITaskException
from api.instances.models import Cluster
from models import DataSet, XmlSqoop
from api.base.exceptions import *

@celery.task(base=SqlAlchemyTask)
def import_data(dataset_id, model_id=None, test_id=None, transformer_id=None):
    """
    Import data from database.
    """
    def get_parent_object():
        if model_id is not None:
            return Model.query.get(model_id)
        if test_id is not None:
            return TestResult.query.get(test_id)
        if transformer_id is not None:
            return Transformer.query.get(transformer_id)

    def set_error(err, ds=None, parent=None):
        if ds is not None:
            ds.set_error(err)
        if parent is not None:
            parent.set_error(err)

    obj = get_parent_object()
    dataset = DataSet.query.get(dataset_id)
    if dataset is None:
        set_error("Dataset with id %s not found" % dataset_id, parent=obj)

    dataset.status = dataset.STATUS_IMPORTING
    dataset.save()

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

        def callback(**kwargs):
            jobflow_id = kwargs.get('jobflow_id')  # required
            master_dns = kwargs.get('master_dns', None)
            s3_logs_folder = kwargs.get('s3_logs_folder', None)
            step_number = kwargs.get('step_number', None)
            pig_row = kwargs.get('pig_row', None)

            jobflow_id, master_dns, s3_logs_folder, step_number
            cluster = Cluster.query.filter(
                Cluster.jobflow_id == jobflow_id
            ).first()
            if cluster is None:
                cluster = Cluster(jobflow_id=jobflow_id)
                if master_dns is not None:
                    cluster.master_node_dns = master_dns
                if s3_logs_folder is not None:
                    cluster.logs_folder = s3_logs_folder
                cluster.save()
            dataset.cluster = cluster
            if step_number is not None:
                dataset.pig_step = step_number
            if pig_row is not None:
                dataset.pig_row = pig_row
            dataset.save()
            if master_dns is not None:
                logging.info('Master dns %s' % master_dns)
                cluster.create_ssh_tunnel()

        logging.info("Import dataset using import handler '%s' \
with%s compression", import_handler.name, '' if dataset.compress else 'out')

        dataset.import_handler_xml = import_handler.data
        handler_iterator = import_handler.get_iterator(
            dataset.import_params, callback)

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

        dataset.filesize = long(_get_uncompressed_filesize(dataset.filename))
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
        logging.error('Got exception when import dataset',
                      exc_info=get_task_traceback(exc))
        set_error(exc, ds=dataset, parent=obj)
        raise CloudmlUITaskException(exc.message, exc)

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
            raise CloudmlUIValueError('DataSet not found')
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
        logging.error('Got exception when uploading dataset',
                      exc_info=get_task_traceback(exc))
        dataset.set_error(exc)
        raise CloudmlUITaskException(exc.message, exc)

    logging.info("Dataset using {0!s} uploaded.".format(dataset))
    return [dataset_id]


@celery.task(base=SqlAlchemyTask)
def load_pig_fields(sqoop_id, params):
    """
    Export classification results to database.
    """
    init_logger('load_pig_fields', obj=int(sqoop_id))

    from utils import SCHEMA_INFO_FIELDS, PIG_TEMPLATE, construct_pig_sample
    sqoop = XmlSqoop.query.get(sqoop_id)
    if sqoop is None:
        raise CloudmlUIValueError(
            "Sqoop element with id {0} not found".format(sqoop_id))

    datasource = sqoop.datasource.core_datasource
    sql = """{0} select * from {1} limit 1;
select {2} from INFORMATION_SCHEMA.COLUMNS where table_name = '{1}';
    """.format(sqoop.text.strip(';'), sqoop.table,
               ','.join(SCHEMA_INFO_FIELDS))
    if params:
        try:
            sql = re.sub('#{(\w+)}', '%(\\1)s', sql)
            sql = sql % params
        except (KeyError, ValueError) as e:
            raise CloudmlUIValueError("Can't construct sql query {0}: "
                                      "parameters {1}"
                                      " are invalid.".format(sql, params), e)
    try:
        iterator = datasource._get_iter(sql)
        fields_data = [{key: opt[i] for i, key in enumerate(
                        SCHEMA_INFO_FIELDS)}
                       for opt in iterator]
    except Exception, exc:
        return CloudmlUIValueError(
            "Can't execute the query: {0}. Error: {1}".format(sql, exc), exc)

    fields_str = construct_pig_sample(fields_data)
    return {'fields': fields_data,
            'sample': PIG_TEMPLATE.format(fields_str),
            'sql': sql}


def _get_uncompressed_filesize(filename):
    """
    copied from gzip.py as per
    http://www.gzip.org/zlib/rfc-gzip.html#header-trailer
    http://stackoverflow.com/a/1704576/161718 and
    https://gist.github.com/ozanturksever/4968827
    :param filename: the name of gzipped file
    :return the size of uncompressed file:
    """
    with open(filename, 'rb') as gzfile:
        gzfile.seek(-4, 2)
        return gzip.read32(gzfile)   # may exceed 2GB
