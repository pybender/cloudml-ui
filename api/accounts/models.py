# Authors: Nikolay Melnik <nmelnik@upwork.com>


import logging
from sqlalchemy import func
from sqlalchemy.orm import exc as orm_exc, validates
from api.base.models import BaseMixin, db
from botocore.exceptions import ClientError
from api.amazon_utils import AmazonDynamoDBHelper


dynamodb = AmazonDynamoDBHelper()


class AuthToken(object):
    TABLE_NAME = 'auth_tokens'

    SCHEMA = [{'AttributeName': 'id', 'KeyType': 'HASH'}]
    SCHEMA_TYPES = [{'AttributeName': 'id', 'AttributeType': 'S'}]

    def __init__(self, oauth_token, oauth_token_secret):
        self.id = oauth_token
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret

    def to_dict(self):
        return {
            'id': self.id,
            'oauth_token': self.oauth_token,
            'oauth_token_secret': self.oauth_token_secret
        }

    def save(self):
        data = self.to_dict()
        dynamodb.put_item(self.TABLE_NAME, data)

    @classmethod
    def create_table(cls):
        dynamodb.create_table(cls.TABLE_NAME, cls.SCHEMA, cls.SCHEMA_TYPES)

    @classmethod
    def get_auth(cls, auth_token):
        try:
            return dynamodb.get_item(cls.TABLE_NAME, id=auth_token)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return None
            else:
                raise e

    @classmethod
    def delete(cls, auth_token):
        dynamodb.delete_item(cls.TABLE_NAME, id=auth_token)


class User(BaseMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(200), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    uid = db.Column(db.String(200), nullable=False)
    odesk_url = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    portrait_32_img = db.Column(db.String(200), nullable=True)
    auth_token = db.Column(db.String(200), nullable=False, unique=True)
    created_on = db.Column(db.DateTime, server_default=func.now())
    updated_on = db.Column(db.DateTime, server_default=func.now(),
                           onupdate=func.current_timestamp())

    @validates('email')
    def validate_email(self, key, address):
        assert '@' in address
        return address

    @classmethod
    def get_hash(cls, token):
        import hashlib
        return hashlib.sha224(token).hexdigest()

    @classmethod
    def authenticate(cls, oauth_token, oauth_token_secret, oauth_verifier):
        logging.debug(
            'User Auth: try to authenticate with token %s', oauth_token)
        from auth import OdeskAuth
        auth = OdeskAuth()
        _oauth_token, _oauth_token_secret = auth.authenticate(
            oauth_token, oauth_token_secret, oauth_verifier)
        logging.debug("Got odeskauth: {0}, {1}".format(_oauth_token,
                                                       _oauth_token_secret))
        info = auth.get_my_info(_oauth_token, _oauth_token_secret,
                                oauth_verifier)
        logging.debug("Got my info: {}".format(info))
        user_info = auth.get_user_info(_oauth_token, _oauth_token_secret,
                                       oauth_verifier)
        logging.info(
            'User Auth: authenticating user %s', info['user']['id'])
        try:
            user = User.query.filter_by(
                uid=info['user']['id']).one()
        except orm_exc.NoResultFound:
            user = User()
            user.uid = info['user']['id']
            logging.debug('User Auth: new user %s added', user.uid)

        import uuid
        auth_token = str(uuid.uuid1())
        user.auth_token = cls.get_hash(auth_token)

        user.name = '{0} {1}'.format(
            info['auth_user']['first_name'],
            info['auth_user']['last_name'])
        user.odesk_url = user_info['info']['profile_url']
        user.portrait_32_img = user_info['info']['portrait_32_img']
        user.email = info['user']['email']

        user.save()
        logging.debug("Finished user authenticate")
        return auth_token, user

    @classmethod
    def get_auth_url(cls):
        from auth import OdeskAuth
        auth = OdeskAuth()
        return auth.get_auth_url()

    def __repr__(self):
        return "%s <%s>" % (self.name, self.uid)
