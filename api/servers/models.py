from datetime import datetime

from sqlalchemy.orm import deferred

from api import app
from api.base.models import BaseModel, db
from .config import FOLDER_MODELS, FOLDER_IMPORT_HANDLERS
from api.amazon_utils import AmazonS3Helper
from boto.exception import S3ResponseError


class Server(BaseModel, db.Model):
    """ Represents cloudml-predict server """
    ALLOWED_FOLDERS = [FOLDER_MODELS, FOLDER_IMPORT_HANDLERS]

    PRODUCTION = 'Production'
    STAGING = 'Staging'
    DEV = 'Development'
    TYPES = [PRODUCTION, STAGING, DEV]

    name = db.Column(db.String(200), nullable=False, unique=True)
    description = deferred(db.Column(db.Text))
    ip = db.Column(db.String(200), nullable=False)
    folder = db.Column(db.String(600), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    memory_mb = db.Column(db.Integer, nullable=False, default=0)
    type = db.Column(db.Enum(*TYPES, name='server_types'), default=DEV)

    def list_keys(self, folder=None, params={}):
        path = self.folder.strip('/')
        if folder and folder in self.ALLOWED_FOLDERS:
            path += '/{0!s}'.format(folder)

        objects = []
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        for key in s3.list_keys(path):
            uid = key.name.split('/')[-1]
            key = s3.bucket.get_key(key.name)

            if key.get_metadata('hide') == 'True':
                continue

            # TODO: last_modified problems with amazon s3 and botoo
            # https://github.com/boto/boto/issues/466
            # https://github.com/spulec/moto/issues/146
            # http://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectGET.html
            objects.append({
                'id': uid,
                'object_name': key.get_metadata('object_name'),
                'size': key.size,
                'uploaded_on': key.get_metadata('uploaded_on'),
                'last_modified': str(datetime.strptime(
                    key.last_modified, '%a, %d %b %Y %H:%M:%S %Z')),
                'name': key.get_metadata('name'),
                'object_id': key.get_metadata('id'),
                'object_type': key.get_metadata('type'),
                'user_id': key.get_metadata('user_id'),
                'user_name': key.get_metadata('user_name'),
                'crc32': key.get_metadata('crc32'),
                'server_id': self.id
            })

        sort_by = params.get('sort_by', None)
        order = params.get('order', 'asc')
        if sort_by:
            return sorted(objects,
                          key=lambda x: x[sort_by],
                          reverse=order != 'asc')
        return objects

    def set_key_metadata(self, uid, folder, key, value):
        if self.check_edit_metadata(folder, key, value):
            key_name = '{0}/{1}/{2}'.format(self.folder, folder, uid)
            s3 = AmazonS3Helper(
                bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
            s3.set_key_metadata(key_name, {key: value}, True)

    def check_edit_metadata(self, folder, key, value):
        entities_by_folder = {
            FOLDER_MODELS: 'Model',
            FOLDER_IMPORT_HANDLERS: 'Import Handler'
        }
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
        return True

    def get_key_metadata(self, uid, folder, key):
        key_name = '{0}/{1}/{2}'.format(self.folder, folder, uid)
        s3 = AmazonS3Helper(
            bucket_name=app.config['CLOUDML_PREDICT_BUCKET_NAME'])
        s3key = s3.bucket.get_key(key_name)
        return s3key.get_metadata(key)

    def save(self, commit=True):
        BaseModel.save(self, commit=False)
        if self.is_default:
            Server.query\
                .filter(Server.is_default, Server.name != self.name)\
                .update({Server.is_default: False})
        if commit:
            db.session.commit()

