import logging
import urlparse
import json
import httplib2

from oauth2 import Consumer, Client, Token

from api import app


class AuthException(Exception):
    pass

class OAuthClient(Client):
    '''
    We encounter redirects with odesk. Though httplib2 has follow_all_redirects
    that allows us to simply solve the problem. It has 2 major problems
    1. Unsolicited POST redirects poses secruity danger.
    2. A bug in oauth2 as per https://github.com/simplegeo/python-oauth2/issues/157
    So we have to manage the request redirection ourselves, still we didn't 
    solve issue #1 above
    '''
    def __init__(self, consumer, token=None, cache=None, timeout=None, proxy_info=None):
        super(OAuthClient, self).__init__(consumer, token, cache, timeout, proxy_info)
        self.follow_all_redirects = True
        self.follow_redirects = True

    def request(self, uri, method="GET", body='', headers=None, 
        redirections=httplib2.DEFAULT_MAX_REDIRECTS, connection_type=None):
        return super(OAuthClient, self).request(
            OAuthClient._stripOauthSignature(uri), 
            method, body, headers, redirections, connection_type
        )

    @staticmethod
    def _stripOauthSignature(uri):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
        query = dict(urlparse.parse_qsl(query))
        if query.has_key('oauth_token'):
            return urlparse.urlunparse((scheme, netloc, path, None, None, None))
        else:
            return uri


class Auth(object):
    REQUEST_TOKEN_URL = ''
    REQUEST_TOKEN_METHOD = 'GET'
    ACCESS_TOKEN_URL = ''
    ACCESS_TOKEN_METHOD = 'POST'
    AUTHORIZE_URL = ''

    def __init__(self, consumer_key, consumer_secret):
        self.consumer = Consumer(consumer_key, consumer_secret)

    def get_auth_url(self):
        # 1
        #client = self._create_client()
        #resp, content = client.request(
        #    self.REQUEST_TOKEN_URL,
        #    self.REQUEST_TOKEN_METHOD
        #)
        #if resp['status'] != '200':
        #    raise AuthException("Invalid response {!s}".format(resp['status']))

        # 2
        #client = Client(self.consumer)
        #resp, content = self._make_request(client, self.REQUEST_TOKEN_URL, 
        #    self.REQUEST_TOKEN_METHOD)
        #if resp['status'] != '200':
        #    raise AuthException("Invalid response {!s}".format(resp['status']))

        # 3
        client = OAuthClient(self.consumer)
        resp, content = client.request(
            self.REQUEST_TOKEN_URL,
            self.REQUEST_TOKEN_METHOD
        )
        if resp['status'] != '200':
            raise AuthException("Invalid response {!s}".format(resp['status']))

        request_token = dict(urlparse.parse_qsl(content))

        oauth_token = request_token.get('oauth_token')
        oauth_token_secret = request_token.get('oauth_token_secret')

        if not oauth_token:
            raise AuthException('There\'s no oauth_token')

        if not oauth_token_secret:
            raise AuthException('There\'s no oauth_token_secret')

        return '{0!s}?oauth_token={1!s}'.format(
            self.AUTHORIZE_URL,
            oauth_token
        ), oauth_token, oauth_token_secret

    def authenticate(self, oauth_token, oauth_token_secret, oauth_verifier):
        token = Token(oauth_token, oauth_token_secret)
        token.set_verifier(oauth_verifier)

        # 1
        #client = self._create_client(token)
        #resp, content = client.request(
        #    self.ACCESS_TOKEN_URL,
        #    self.ACCESS_TOKEN_METHOD
        #)
        #if resp['status'] != '200':
        #    raise AuthException('Authentication failed: {0!s}'.format(content))

        # 2
        #lient = Client(self.consumer, token)
        #esp, content = self._make_request(client, self.ACCESS_TOKEN_URL, 
        #   self.ACCESS_TOKEN_METHOD)
        #f resp['status'] != '200':
        #   raise AuthException('Authentication failed: {0!s}'.format(content))

        # 3
        client = OAuthClient(self.consumer, token)
        resp, content = client.request(
            self.ACCESS_TOKEN_URL,
            self.ACCESS_TOKEN_METHOD
        )
        if resp['status'] != '200':
            raise AuthException("Invalid response {!s}".format(resp['status']))

        access_token = dict(urlparse.parse_qsl(content))
        return (
            access_token['oauth_token'],
            access_token['oauth_token_secret'])

    def _make_request(self, client, url, method, body='', headers=None, redir_count=4):
        '''
        We encounter redirects with odesk. Though httplib2 has follow_all_redirects
        that allows us to simply solve the problem. It has 2 major problems
        1. Unsolicited POST redirects poses secruity danger.
        2. A bug in oauth2 as per https://github.com/simplegeo/python-oauth2/issues/157
        So we have to manage the request redirection ourselves, still we didn't 
        solve issue #1 above
        '''
        client.follow_all_redirects = False
        client.follow_redirects = False
        resp, content = client.request(url, method, body, headers)
        logging.debug('making request to url:%s, method:%s', url, method)
        if resp['status'] in ['300', '301', '302', '303', '307'] and redir_count > 0:
            logging.debug('a redirct detected, status:%s, from:%s, to:%s', 
                resp['status'], url, resp.get('location', 'NO LOCATION KEY IN RESPONSE'))
            if resp.has_key('location'):
                toUrl = resp['location']
                scheme, authority, path, params, query, fragment = \
                    urlparse.urlparse(toUrl)
                if authority == None:
                    scheme, authority, _, _, _, _ = urlparse.urlparse(url)
                toUrl = urlparse.urlunsplit((scheme, authority, path, None, None))
                logging.debug('following a redirect from url:%s, to url:%s',
                    url, toUrl)
                return self._make_request(client, toUrl, method, body, 
                    headers, redir_count-1)

        return resp, content
    def _create_client(self, token=None):
        '''
        Creates a oauth2 client, applies common configuration to it using the
        current self.Consumer
        @token: Can be None
        '''
        client = Client(self.consumer, token)
        # TODO: Unsolicited redirects is a security problem in case of oauth2
        # server is compromised, and will cause token leaks. A better approach
        # to create our own client class that handles ciritcal redirs by screening
        # them first and then conditionally follow the redir or reject it. 
        client.follow_all_redirects = True
        return client


class OdeskAuth(Auth):
    REQUEST_TOKEN_URL = 'http://www.odesk.com/api/auth/v1/oauth/token/request'
    REQUEST_TOKEN_METHOD = 'POST'

    ACCESS_TOKEN_URL = 'http://www.odesk.com/api/auth/v1/oauth/token/access'
    ACCESS_TOKEN_METHOD = 'POST'
    AUTHORIZE_URL = 'http://www.odesk.com/services/api/auth'

    GET_INFO_URL = 'http://www.odesk.com/api/hr/v2/users/me'
    GET_USER_INFO_URL = 'https://www.odesk.com/api/auth/v1/info'

    def __init__(self):
        super(OdeskAuth, self).__init__(
            app.config['ODESK_OAUTH_KEY'],
            app.config['ODESK_OAUTH_SECRET'],
        )

    def api_request(self, url, method, oauth_token, oauth_token_secret,
                    oauth_verifier):
        token = Token(oauth_token, oauth_token_secret)
        token.set_verifier(oauth_verifier)

        # 1
        #client = self._create_client(token)
        #resp, content = client.request(
        #    '{0}.json'.format(url),
        #    method
        #)
        #if resp['status'] != '200':
        #    raise AuthException('Getting info failed url:{0!s} content: {1!s}'.
        #        format(url, content))

        # 2
        #Client = Client(self.consumer, token)
        #resp, content = self._make_request(client, '{0}.json'.format(url), 
        #   method)
        #if resp['status'] != '200':
        #   raise AuthException('Getting info failed url:{0!s} content: {1!s}'.
        #       format(url, content))

        # 3
        client = OAuthClient(self.consumer, token)
        resp, content = client.request(
            '{0}.json'.format(url),
            method
        )
        if resp['status'] != '200':
            raise AuthException('Getting info failed url:{0!s} content: {1!s}'.
                format(url, content))

        return json.loads(content)

    def get_my_info(self, oauth_token, oauth_token_secret, oauth_verifier):
        return self.api_request(self.GET_INFO_URL, 'GET',
                                oauth_token, oauth_token_secret,
                                oauth_verifier)
    def get_user_info(self, oauth_token, oauth_token_secret, oauth_verifier):
        return self.api_request(self.GET_USER_INFO_URL, 'GET',
                                oauth_token, oauth_token_secret,
                                oauth_verifier)
