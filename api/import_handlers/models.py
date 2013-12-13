import json
import logging
from boto.exception import S3ResponseError
import os
from os.path import join, exists
from os import makedirs
import StringIO

from sqlalchemy.orm import relationship, deferred, backref
from sqlalchemy.dialects import postgresql

from api import app
from api.amazon_utils import AmazonS3Helper
from api.base.models import db, BaseModel, JSONType
from api.logs.models import LogMessage


class ImportHandler(db.Model, BaseModel):
    TYPE_DB = 'Db'
    TYPE_REQUEST = 'Request'

    TYPES = (TYPE_DB, TYPE_REQUEST)

    __tablename__ = 'import_handler'

    name = db.Column(db.String(200))
    type = db.Column(db.Enum(*TYPES, name='handler_types'))
    data = deferred(db.Column(JSONType))
    import_params = db.Column(postgresql.ARRAY(db.String))

    def get_fields(self):
        from core.importhandler.importhandler import ExtractionPlan

        data = json.dumps(self.data)
        plan = ExtractionPlan(data, is_file=False)
        test_handler_fields = []
        for query in plan.queries:
            items = query['items']
            for item in items:
                features = item['target-features']
                for feature in features:
                    test_handler_fields.append(
                        feature['name'].replace('.', '->'))
        return test_handler_fields

    def create_dataset(self, params, run_import_data=True, data_format='json'):
        dataset = DataSet()
        str_params = "-".join(["%s=%s" % item
                               for item in params.iteritems()])
        dataset.name = "%s: %s" % (self.name, str_params)
        dataset.import_handler_id = self.id
        dataset.import_params = params
        dataset.format = data_format
        dataset.save()
        dataset.set_file_path()
        return dataset

    def __repr__(self):
        return '<Import Handler %r>' % self.name



# @app.conn.register
# class ImportHandler(BaseDocument):
#     __collection__ = 'handlers'
#     QUERY_STRUCT = {
#         "name": basestring,
#         "sql": basestring,
#         "items": [{"target_features": [{}]}]
#     }

#     structure = {
#         'name': basestring,
#         'error': basestring,
#         "import_params": list,
#         'created_on': datetime,
#         'created_by': dict,
#         'updated_on': datetime,
#         'updated_by': dict,

#         # FIXME: Investigate, why when spec struct of dict,
#         # data always returns using find or find_one mthd.
#         'data': {
#             'target_schema': basestring,
#             'datasource': list,
#             'queries': list
#         },
#         #'data': dict,
#     }

#     use_dot_notation = True
#     required_fields = ['name', 'created_on', ]
#     default_values = {'created_on': datetime.utcnow,
#                       'updated_on': datetime.utcnow,
#                       'data.datasource': [],
#                       'data.queries': [],
#                       'data.target_schema': ''}

#     def set_target_schema(self, val):
#         self.data['target_schema'] = val

#     def get_target_schema(self):
#         return self.data['target_schema']

#     target_schema = property(get_target_schema, set_target_schema)

#     def save(self, *args, **kwargs):
#         self.error = ''
#         try:
#             plan = ExtractionPlan(json.dumps(self.data), is_file=False)
#             self.import_params = plan.input_params
#         except Exception as e:
#             self.error = str(e)
#         super(ImportHandler, self).save(*args, **kwargs)

#     def from_import_handler_json(self, data):
#         self.target_schema = data['target_schema']
#         self.data['queries'] = data['queries']
#         self.data['datasource'] = data['datasource']
#         self.save()

#     def validate(self, *args, **kwargs):
#         def validate_structure(item, struct):
#             for key, val in struct.iteritems():
#                 if type(val) == dict:
#                     validate_structure(item[key], val)
#                 elif type(val) == list:
#                     for subitem in item[key]:
#                         validate_structure(subitem, val[0])
#                 else:
#                     assert key in item, '%s is required' % key

#         super(ImportHandler, self).validate(*args, **kwargs)
#         for query in self.data['queries']:
#             validate_structure(query, self.QUERY_STRUCT)

#     SYSTEM_FIELDS = ('_id', 'created_on', 'created_by',
#         'updated_on', 'updated_by', 'import_params', 'error')

#     # @property
#     # def data(self):
#     #     from copy import deepcopy
#     #     data = deepcopy(dict(self))
#     #     for field in self.SYSTEM_FIELDS:
#     #         data.pop(field, None)

#     #     for ds in data['datasource']:
#     #         ds['db'] = ds.pop('db_settings', None)
#     #     return data

#     # TODO: Denormalize to field!
#     def get_fields(self):
#         data = json.dumps(self.data)
#         plan = ExtractionPlan(data, is_file=False)
#         test_handler_fields = []
#         for query in plan.queries:
#             items = query['items']
#             for item in items:
#                 features = item['target_features']
#                 for feature in features:
#                     test_handler_fields.append(
#                         feature['name'].replace('.', '->'))
#         return test_handler_fields

#     def create_dataset(self, params, run_import_data=True, data_format='json'):
#         #from api.utils import slugify
#         dataset = app.db.DataSet()
#         str_params = "-".join(["%s=%s" % item
#                               for item in params.iteritems()])
#         dataset.name = "%s: %s" % (self.name, str_params)
#         dataset.import_handler_id = str(self._id)
#         dataset.import_params = params
#         dataset.format = data_format
#         # filename = '%s-%s.json' % (slugify(self.name)
#         # str_params.replace('=', '_'))
#         # dataset.data = filename
#         dataset.save(validate=True)
#         dataset.set_file_path()
#         return dataset

#     def delete(self):
#         datasets = app.db.DataSet.find({'import_handler_id': str(self._id)})
#         for ds in datasets:
#             ds.delete()

#         expr = {'$or': [{'test_import_handler.$id': self._id},
#                         {'train_import_handler.$id': self._id}]}
#         models = app.db.Model.find(expr)

#         def unset(model, handler_type='train'):
#             handler = getattr(model, '%s_import_handler' % handler_type)
#             if handler and handler['_id'] == self._id:
#                 setattr(model, '%s_import_handler' % handler_type, None)
#                 model.changed = True

#         for model in models:
#             model.changed = False
#             unset(model, 'train')
#             unset(model, 'test')
#             if model.changed:
#                 model.save()

#         super(ImportHandler, self).delete()

#     def check_sql(self, sql):
#         """
#         Parses sql query structure from text,
#         raises Exception if it's not a SELECT query or invalid sql.
#         """
#         import sqlparse

#         query = sqlparse.parse(sql)
#         wrong_sql = False
#         if len(query) < 1:
#             wrong_sql = True
#         else:
#             query = query[0]
#             if query.get_type() != 'SELECT':
#                 wrong_sql = True

#         if wrong_sql:
#             raise Exception('Invalid sql query')
#         else:
#             return query

#     def build_query(self, sql, limit=2):
#         """
#         Parses sql query and changes LIMIT statement value.
#         """
#         import re
#         from sqlparse import parse, tokens
#         from sqlparse.sql import Token

#         # It's important to have a whitespace right after every LIMIT
#         pattern = re.compile('limit([^ ])', re.IGNORECASE)
#         sql = pattern.sub(r'LIMIT \1', sql)

#         query = parse(sql)[0]

#         # Find LIMIT statement
#         token = query.token_next_match(0, tokens.Keyword, 'LIMIT')
#         if token:
#             # Find and replace LIMIT value
#             value = query.token_next(query.token_index(token), skip_ws=True)
#             if value:
#                 new_token = Token(value.ttype, str(limit))
#                 query.tokens[query.token_index(value)] = new_token
#         else:
#             # If limit is not found, append one
#             new_tokens = [
#                 Token(tokens.Whitespace, ' '),
#                 Token(tokens.Keyword, 'LIMIT'),
#                 Token(tokens.Whitespace, ' '),
#                 Token(tokens.Number, str(limit)),
#             ]
#             last_token = query.tokens[-1]
#             if last_token.ttype == tokens.Punctuation:
#                 query.tokens.remove(last_token)
#             for new_token in new_tokens:
#                 query.tokens.append(new_token)

#         return str(query)

#     def execute_sql_iter(self, sql, datasource_name):
#         """
#         Executes sql using data source with name datasource_name.
#         Datasource with given name should be in handler's datasource list.
#         Returns iterator.
#         """
#         from core.importhandler import importhandler
#         datasource = next((d for d in self.data['datasource']
#                            if d['name'] == datasource_name))

#         iter_func = importhandler.ImportHandler.DB_ITERS.get(
#             datasource['db']['vendor'])

#         for row in iter_func([sql], datasource['db']['conn']):
#             yield dict(row)

#     def __repr__(self):
#         return '<Import Handler %r>' % self.name



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
    error = db.Column(db.String(200))
    data = db.Column(db.String(200))
    import_params = db.Column(JSONType)

    import_handler_id = db.Column(db.Integer,
                                  db.ForeignKey('import_handler.id'))
    import_handler = relationship('ImportHandler', backref=backref(
        'datasets', cascade='all,delete'))

    on_s3 = db.Column(db.Boolean)
    compress = db.Column(db.Boolean)
    filename = db.Column(db.String(200))
    filesize = db.Column(db.BigInteger)
    records_count = db.Column(db.Integer)
    time = db.Column(db.Integer)
    data_fields = db.Column(postgresql.ARRAY(db.String))
    current_task_id = db.Column(db.String(100))
    format = db.Column(db.String(10))

    def get_s3_download_url(self, expires_in=3600):
        helper = AmazonS3Helper()
        return helper.get_download_url(str(self.id), expires_in)

    def set_file_path(self):
        data = '%s.%s' % (self.id, 'gz' if self.compress else 'json')
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
            stream = StringIO.StringIO(self.data)
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
        return helper.load_key(str(self.id))

    def save_to_s3(self):
        meta = {'handler': self.import_handler_id,
                'dataset': self.name,
                'params': str(self.import_params)}
        helper = AmazonS3Helper()
        helper.save_gz_file(str(self.id), self.filename, meta)
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
        ds_id = self.id
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
                helper.delete_key(str(ds_id))
            except S3ResponseError as e:
                logging.exception(str(e))

    def save(self, *args, **kwargs):
        if self.status != self.STATUS_ERROR:
            self.error = ''
        super(DataSet, self).save(*args, **kwargs)

    def __repr__(self):
        return '<Dataset %r>' % self.name
