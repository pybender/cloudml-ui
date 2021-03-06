from sqlalchemy.orm import relationship, deferred, backref
from api import app
from api.base.models import BaseModel, db, JSONType, BaseMixin
from api.ml_models.models import Model
from api.import_handlers.models import RefXmlImportHandlerMixin, \
    XmlImportHandler
from api.model_tests.models import TestResult
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS
from api.amazon_utils import AmazonS3Helper
import urllib


class Server(BaseModel, db.Model):
    """ Represents cloudml-predict server """
    ALLOWED_FOLDERS = [FOLDER_MODELS, FOLDER_IMPORT_HANDLERS]

    PRODUCTION = 'Production'
    STAGING = 'Staging'
    DEV = 'Development'
    ANALYTICS = 'Analytics'
    TYPES = [STAGING, DEV, ANALYTICS, PRODUCTION]

    ENV_MAP = {
        PRODUCTION: 'prod',
        STAGING: 'staging',
        DEV: 'dev',
        ANALYTICS: 'analytics'}

    name = db.Column(db.String(200), nullable=False, unique=True)
    description = deferred(db.Column(db.Text))
    ip = db.Column(db.String(200), nullable=False)
    folder = db.Column(db.String(600), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    memory_mb = db.Column(db.Integer, nullable=False, default=0)
    type = db.Column(db.Enum(*TYPES, name='server_types'), default=DEV)
    logs_url = db.Column(db.Text)

    def __repr__(self):
        return '<Server {0}>'.format(self.name)

    @property
    def grafana_name(self):
        if not hasattr(self, '_grafana_name'):
            from slugify import slugify
            name = self.name.replace('_', '-')
            self._grafana_name = slugify('CloudMl ' + name)
        return self._grafana_name

    @property
    def grafana_url(self):
        from api import app
        return 'http://{0}/dashboard/db/{1}'.format(
            app.config.get('GRAFANA_HOST'),
            self.grafana_name)

    def list_keys(self, folder=None, params={}):
        path = self.folder.strip('/')
        if folder and folder in self.ALLOWED_FOLDERS:
            path += '/{0!s}'.format(folder)

        objects = []
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        for key in s3.list_keys(path):
            uid = key['Key'].split('/')[-1]
            key = s3.load_key(key['Key'], with_metadata=True)

            if key['Metadata']['hide'] == 'True':
                continue

            objects.append({
                'id': uid,
                'object_name': key['Metadata'].get('object_name', None),
                'size': key['ContentLength'],
                'uploaded_on': key['Metadata'].get('uploaded_on', None),
                'last_modified': str(key['LastModified']),
                'name': key['Metadata'].get('name', None),
                'object_id': key['Metadata'].get('id', None),
                'object_type': key['Metadata'].get('type', None),
                'user_id': key['Metadata'].get('user_id', None),
                'user_name': key['Metadata'].get('user_name', None),
                'crc32': key['Metadata'].get('crc32', None),
                'server_id': self.id,
                'loading_error': key['Metadata'].get('loading_error', None),
                'count_400': key['Metadata'].get('count_400', None),
                'count_500': key['Metadata'].get('count_500', None),
                'count_of_max_response': key['Metadata'].get(
                    'count_of_max_response', None),
                'longest_resp_count': key['Metadata'].get('longest_resp_count',
                                                          None),
                'longest_resp_time': key['Metadata'].get('longest_resp_time',
                                                         None),
                'max_response_time': key['Metadata'].get('max_response_time',
                                                         None),
                'requests': key['Metadata'].get('requests', None)
            })

        sort_by = params.get('sort_by', None)
        order = params.get('order', 'asc')
        if objects and sort_by:
            obj = objects[0]
            if sort_by in obj.keys():
                return sorted(objects,
                              key=lambda x: x[sort_by],
                              reverse=order != 'asc')
            else:
                raise ValueError('Unable to sort by %s. Property is not exist.'
                                 % sort_by)
        return objects

    def set_key_metadata(self, uid, folder, key, value):
        if self.check_edit_metadata(folder, key, value):
            key_name = '{0}/{1}/{2}'.format(self.folder, folder, uid)
            s3 = AmazonS3Helper(
                bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
            s3.set_key_metadata(key_name, {key: value}, True)
            # this means key is deleted, need to update model/import handler
            if key == 'hide' and value == 'True':
                obj = s3.load_key(key_name, with_metadata=True)
                cl = Model if folder == FOLDER_MODELS else XmlImportHandler
                model = cl.query.get(obj['Metadata']['id'])
                server_list = [s for s in model.servers_ids if s != self.id]
                model.servers_ids = server_list
                model.save()

    def check_edit_metadata(self, folder, key, value):
        entities_by_folder = {
            FOLDER_MODELS: 'Model',
            FOLDER_IMPORT_HANDLERS: 'Import Handler'
        }
        integer_keys = ['count_400', 'count_500', 'count_of_max_response']
        entity = entities_by_folder.get(folder, None)
        if not entity:
            raise ValueError('Wrong folder: %s' % folder)

        if key == 'name':
            files = self.list_keys(folder)
            for file_ in files:
                if file_['name'] == value:
                    raise ValueError('{0} with name "{1}" already exists on '
                                     'the server {2}'.format(entity, value,
                                                             self.name))
        if key in integer_keys:
            try:
                v = int(value)
            except Exception:
                raise ValueError("Incorrect value '{0}' for '{1}'. Integer is "
                                 "expected".format(value, key))
        return True

    def get_key_metadata(self, uid, folder, key):
        key_name = '{0}/{1}/{2}'.format(self.folder, folder, uid)
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        s3key = s3.load_key(key_name, with_metadata=True)
        return s3key['Metadata'][key]

    def save(self, commit=True):
        BaseModel.save(self, commit=False)
        if self.is_default:
            Server.query\
                .filter(Server.is_default, Server.name != self.name)\
                .update({Server.is_default: False})
        if commit:
            db.session.commit()


class ServerModelVerification(BaseModel, db.Model,
                              RefXmlImportHandlerMixin):
    """
    Represents verification of the model,
    that deployed to the server
    """
    STATUS_NEW = 'New'
    STATUS_QUEUED = 'Queued'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_ERROR = 'Error'
    STATUS_DONE = 'Done'

    STATUSES = [STATUS_NEW, STATUS_QUEUED,
                STATUS_IN_PROGRESS, STATUS_ERROR,
                STATUS_DONE]

    status = db.Column(
        db.Enum(*STATUSES, name='model_verification_statuses'),
        nullable=False, default=STATUS_NEW)
    error = db.Column(db.Text)
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'))
    server = relationship(
        Server, backref=backref('model_verifications', cascade='all,delete'))
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    model = relationship(
        Model, backref=backref('model_verifications', cascade='all,delete'))
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_result.id'))
    test_result = relationship(
        'TestResult',
        backref=backref('model_verifications',
                        cascade='all,delete'))
    description = db.Column(JSONType)
    result = db.Column(JSONType)
    params_map = db.Column(JSONType)
    clazz = db.Column(db.String(200))

    def __repr__(self):
        return '<ServerModelVerification {0}>'.format(self.model.name)


class VerificationExample(BaseMixin, db.Model):
    verification_id = db.Column(
        db.Integer, db.ForeignKey('server_model_verification.id'))
    verification = relationship(
        'ServerModelVerification',
        backref=backref('verification_examples',
                        cascade='all,delete'))

    example_id = db.Column(db.Integer, db.ForeignKey('test_example.id'))
    example = relationship(
        'TestExample',
        backref=backref('verification_examples',
                        cascade='all,delete'))

    result = db.Column(JSONType)
