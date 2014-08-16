import logging
from flask.ext.restful import reqparse
from flask import request

from api import app, api
from api.base.resources import BaseResourceSQL, NotFound, \
    odesk_error_response, public
from models import User, AuthToken

from api.amazon_utils import AmazonDynamoDBHelper


db = AmazonDynamoDBHelper()


class AuthResource(BaseResourceSQL):
    """ User API methods """
    ALLOWED_METHODS = ('post', 'options')

    @public
    def post(self, action=None, **kwargs):
        if action == 'get_auth_url':
            auth_url, oauth_token, oauth_token_secret =\
                User.get_auth_url()

            # TODO: Use redis?
            # app.db['auth_tokens'].insert({
            #     'oauth_token': oauth_token,
            #     'oauth_token_secret': oauth_token_secret,
            # })
            auth = AuthToken(oauth_token, oauth_token_secret)
            auth.save()

            logging.debug(
                "User Auth: oauth token %s added to mongo", oauth_token)
            return self._render({'auth_url': auth_url})

        if action == 'authenticate':
            parser = reqparse.RequestParser()
            parser.add_argument('oauth_token', type=str)
            parser.add_argument('oauth_verifier', type=str)
            params = parser.parse_args()

            oauth_token = params.get('oauth_token')
            oauth_verifier = params.get('oauth_verifier')

            logging.debug(
                "User Auth: trying to authenticate with token %s", oauth_token)
            # TODO: Use redis?
            auth = AuthToken.get_auth(oauth_token)
            if not auth:
                logging.error('User Auth: token %s not found', oauth_token)
                return odesk_error_response(
                    500, 500,
                    'Wrong token: {0!s}'.format(oauth_token))

            oauth_token_secret = auth.get('oauth_token_secret')
            auth_token, user = User.authenticate(
                oauth_token, oauth_token_secret, oauth_verifier)

            logging.debug(
                'User Auth: Removing token %s from mongo', oauth_token)
            AuthToken.delete(auth.get('oauth_token'))

            return self._render({
                'auth_token': auth_token,
                'user': user
            })

        if action == 'get_user':
            user = getattr(request, 'user', None)
            if user:
                return self._render({'user': user})

            return odesk_error_response(401, 401, 'Unauthorized')

        logging.error('User Auth: invalid action %s', action)
        raise NotFound()

api.add_resource(AuthResource, '/cloudml/auth/<regex("[\w\.]*"):action>',
                 add_standard_urls=False)
