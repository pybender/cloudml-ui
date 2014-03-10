import json
import logging
import os
import StringIO
import uuid
from os.path import join, exists
from os import makedirs

from boto.exception import S3ResponseError
from sqlalchemy.orm import relationship, deferred, backref, validates
from sqlalchemy.dialects import postgresql

from api import app
from api.amazon_utils import AmazonS3Helper
from api.base.models import db, BaseModel, JSONType, assertion_msg
from api.logs.models import LogMessage


class DataSet(db.Model, BaseModel):
    LOG_TYPE = LogMessage.IMPORT_DATA

    STATUS_IMPORTING = 'Importing'
    STATUS_UPLOADING = 'Uploading'
    STATUS_IMPORTED = 'Imported'
    STATUS_ERROR = 'Error'
    STATUSES = [STATUS_IMPORTING, STATUS_UPLOADING, STATUS_IMPORTED,
                STATUS_ERROR]

    FORMAT_JSON = 'json'
    FORMAT_CSV = 'csv'
    FORMATS = [FORMAT_JSON, FORMAT_CSV]

    name = db.Column(db.String(200))
    status = db.Column(db.Enum(*STATUSES, name='dataset_statuses'))
    error = db.Column(db.String(300))  # TODO: trunc error to 300 symbols
    data = db.Column(db.String(200))
    import_params = db.Column(JSONType)

    # We will delete old IH in the future
    import_handler_id = db.Column(db.Integer,
                                  db.ForeignKey('import_handler.id'))
    import_handler = relationship('ImportHandler', backref=backref(
        'datasets', cascade='all,delete'))

    xml_import_handler_id = db.Column(
        db.Integer, db.ForeignKey('xml_import_handler.id'))
    xml_import_handler = relationship('XmlImportHandler', backref=backref(
        'datasets', cascade='all,delete'))

    on_s3 = db.Column(db.Boolean)
    compress = db.Column(db.Boolean)
    filename = db.Column(db.String(200))
    filesize = db.Column(db.BigInteger)
    records_count = db.Column(db.Integer)
    time = db.Column(db.Integer)
    data_fields = db.Column(postgresql.ARRAY(db.String))
    format = db.Column(db.String(10))
    uid = db.Column(db.String(200))

    def set_uid(self):
        if not self.uid:
            self.uid = uuid.uuid1().hex

    def get_s3_download_url(self, expires_in=3600):
        helper = AmazonS3Helper()
        return helper.get_download_url(self.uid, expires_in)

    def set_file_path(self):
        self.set_uid()
        data = '%s.%s' % (self.uid, 'gz' if self.compress else 'json')
        self.data = data
        path = app.config['DATA_FOLDER']
        if not exists(path):
            makedirs(path)
        self.filename = join(path, data)
        self.save()

    @property
    def loaded_data(self):
        if not self.on_s3:
            raise Exception('Invalid oper')

        if not hasattr(self, '_data'):
            self._data = self.load_from_s3()
        return self._data

    def get_data_stream(self):
        import gzip
        #import zlib
        if not self.on_s3 or exists(self.filename):
            logging.info('Loading data from local file')
            open_meth = gzip.open if self.compress else open
            return open_meth(self.filename, 'r')
        else:
            logging.info('Loading data from Amazon S3')
            stream = StringIO.StringIO(self.loaded_data)
            if self.compress:
                logging.info('Decompress data')
                return gzip.GzipFile(fileobj=stream, mode='r')
                #data = zlib.decompress(data)
            return stream

    def get_iterator(self, stream):
        from core.trainer.streamutils import streamingiterload

        return streamingiterload(stream, source_format=self.format)

    def load_from_s3(self):
        helper = AmazonS3Helper()
        return helper.load_key(self.uid)

    def save_to_s3(self):
        meta = {'handler': self.import_handler_id,
                'dataset': self.name,
                'params': str(self.import_params)}
        self.set_uid()
        helper = AmazonS3Helper()
        helper.save_gz_file(self.uid, self.filename, meta)
        helper.close()
        self.on_s3 = True
        self.save()

    def set_error(self, error, commit=True):
        self.error = str(error)
        self.status = self.STATUS_ERROR
        if commit:
            self.save()

    def delete(self):
        # Stop task
        # self.terminate_task()  # TODO
        filename = self.filename
        on_s3 = self.on_s3

        super(DataSet, self).delete()
        LogMessage.delete_related_logs(self)

        # TODO: check import handler type
        try:
            os.remove(filename)
        except OSError:
            pass
        if on_s3:
            from api.amazon_utils import AmazonS3Helper
            helper = AmazonS3Helper()
            try:
                helper.delete_key(self.uid)
            except S3ResponseError as e:
                logging.exception(str(e))

    def save(self, *args, **kwargs):
        if self.status != self.STATUS_ERROR:
            self.error = ''
        super(DataSet, self).save(*args, **kwargs)

    def __repr__(self):
        return '<Dataset %r>' % self.name
