# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
from unittest import TestCase
from mock import patch, Mock

from api import app

from api.base.test_utils import BaseDbTestCase
from models import AuthToken, User


UPWORK_URL = 'www.upwork.com'
AUTH_TOKEN = '123'
HTTP_HEADERS = [('X-Auth-Token', AUTH_TOKEN)]


class AuthDecoratorsTests(BaseDbTestCase):
    """
    Tests of the authentication system.
    """
    def test_auth_decorators(self):
        from api.base.resources.decorators import authenticate, public,\
            public_actions

        def _view(_argument, action=None):
            return app.response_class(_argument,
                                      mimetype='application/json', status=200)

        # Unauthorized
        with app.test_request_context('/') as ctx:
            req = ctx.request

            view = authenticate(_view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample')
            self.assertEquals(res.status_code, 401)
            self.assertEquals(res.headers['X-Odesk-Error-Message'],
                              'Unauthorized')
            self.assertFalse(hasattr(req, 'user'))

        # Authorized
        if hasattr(_view, 'authenticated'):
            delattr(_view, 'authenticated')
        with app.test_request_context('/', headers=HTTP_HEADERS) as ctx:
            req = ctx.request

            view = authenticate(_view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample')
            self.assertEquals(res.status_code, 200)
            self.assertEquals(res.data, 'sample')
            self.assertEquals(str(req.user.uid), 'somebody')

        # Wrong auth token
        headers = dict(HTTP_HEADERS)
        headers['X-Auth-Token'] = 'wrong'
        if hasattr(_view, 'authenticated'):
            delattr(_view, 'authenticated')
        with app.test_request_context('/', headers=headers.items()) as ctx:
            req = ctx.request

            view = authenticate(_view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample')
            self.assertEquals(res.status_code, 401)
            self.assertEquals(res.headers['X-Odesk-Error-Message'],
                              'Unauthorized')
            self.assertIsNone(req.user)

        # Public view
        if hasattr(_view, 'authenticated'):
            delattr(_view, 'authenticated')
        with app.test_request_context('/') as ctx:
            req = ctx.request

            view = public(_view)
            self.assertTrue(hasattr(view, 'authenticated'))
            self.assertTrue(view.authenticated)

            view = authenticate(view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample')
            self.assertEquals(res.status_code, 200)
            self.assertEquals(res.data, 'sample')
            self.assertFalse(hasattr(req, 'user'))

        # Public actions
        if hasattr(_view, 'authenticated'):
            delattr(_view, 'authenticated')
        with app.test_request_context('/') as ctx:
            req = ctx.request

            view = public_actions(['act1', 'act2'])(_view)
            self.assertTrue(hasattr(view, 'public_actions'))

            view = authenticate(view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample', action='act1')
            self.assertEquals(res.status_code, 200)
            self.assertEquals(res.data, 'sample')
            self.assertFalse(hasattr(req, 'user'))

            res = view('sample', action='act2')
            self.assertEquals(res.status_code, 200)
            self.assertEquals(res.data, 'sample')
            self.assertFalse(hasattr(req, 'user'))

            res = view('sample')
            self.assertEquals(res.status_code, 401)

            res = view('sample', action='some_other')
            self.assertEquals(res.status_code, 401)


class AuthTokenModelTests(BaseDbTestCase):
    def setUp(self):
        super(AuthTokenModelTests, self).setUp()

    def tearDown(self):
        BaseDbTestCase.tearDown(self)

    @patch('api.amazon_utils.AmazonDynamoDBHelper.put_item')
    @patch('api.amazon_utils.AmazonDynamoDBHelper.get_item')
    @patch('api.amazon_utils.AmazonDynamoDBHelper.delete_item')
    def test_token(self, delete_mock, get_mock, put_mock):
        TOKEN = '394c46b8902fb5e8fc9268f3cfd84539'
        SECRET = '394c46b8902fb5e8fc9268f3cfd84538'
        token_dict = dict(oauth_token=TOKEN, oauth_token_secret=SECRET,
                          id=TOKEN)

        token = AuthToken(
            oauth_token=TOKEN,
            oauth_token_secret=SECRET)
        self.assertEquals(token.to_dict(), token_dict)
        token.save()
        put_mock.assert_called_with(token.TABLE_NAME, token_dict)

        get_mock.return_value = None
        self.assertEquals(AuthToken.get_auth('invalid'), None)

        # get_item
        get_mock.return_value = token_dict
        self.assertEquals(AuthToken.get_auth(TOKEN), token_dict)

        # delete
        AuthToken.delete(TOKEN)
        delete_mock.assert_called_with(token.TABLE_NAME, id=TOKEN)
        get_mock.return_value = None
        self.assertEquals(AuthToken.get_auth('invalid'), None)


class AuthResourceTests(BaseDbTestCase):
    """
    Tests of the authentication system.
    """

    BASE_URL = '/cloudml/auth'

    def setUp(self):
        BaseDbTestCase.setUp(self)

    def tearDown(self):
        BaseDbTestCase.tearDown(self)

    @patch('api.accounts.models.User.get_auth_url',
           return_value=('url', '1', '2'))
    @patch('api.accounts.models.AuthToken.save')
    def test_get_auth_url(self, mock, mock_auth):
        url = '{0}/get_auth_url'.format(self.BASE_URL)
        resp = self.client.post(url, data={})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(mock_auth.call_count, 1)
        data = json.loads(resp.data)
        self.assertTrue('auth_url' in data)
        self.assertEquals(data['auth_url'], 'url')
        # secret = app.db['auth_tokens'].find_one({'oauth_token': '1'})
        # self.assertIsNotNone(secret)
        # self.assertEquals(secret.get('oauth_token_secret'), '2')

    def test_invalid_action_or_method(self):
        url = '{0}/invalid_action?oauth_token={1}&oauth_verifier={2}'.format(
            self.BASE_URL, '123', '345'
        )

        resp = self.client.post(url, data={})
        self.assertEquals(resp.status_code, 404)

        url = '{0}/get_auth_url'.format(self.BASE_URL)
        resp = self.client.get(url, data={})
        self.assertEquals(resp.status_code, 400)

        url = '{0}/get_auth_url'.format(self.BASE_URL)
        resp = self.client.put(url, data={})
        self.assertEquals(resp.status_code, 400)

    @patch('api.accounts.models.AuthToken.get_auth',
           return_value=None)
    @patch('api.accounts.models.AuthToken.delete')
    def test_authenticate(self, mock_delete, mock_get_auth):
        url = '{0}/authenticate?oauth_token={1}&oauth_verifier={2}'.format(
            self.BASE_URL, '123', '345'
        )

        # Wrong token
        resp = self.client.post(url, data={})
        self.assertEquals(resp.status_code, 500)
        self.assertEquals(resp.headers['X-Odesk-Error-Message'],
                          'Wrong token: 123')

        with patch('api.accounts.models.User.authenticate',
                   return_value=(
                       '123',
                       User.query.filter_by(uid='somebody').one())
                   ) as mock_auth:

            # Proper token

            mock_get_auth.return_value = {
                'oauth_token': '123',
                'oauth_token_secret': '999',
            }

            resp = self.client.post(url, data={})
            self.assertEquals(mock_auth.call_count, 1)
            data = json.loads(resp.data)
            self.assertTrue('auth_token' in data)
            self.assertTrue(data['auth_token'])
            self.assertTrue('user' in data)
            self.assertTrue(data['user'])
            self.assertEquals(data['user']['uid'], 'somebody')

    def test_get_user(self):
        url = '{0}/get_user'.format(self.BASE_URL)

        # Unauthorized
        resp = self.client.post(url)
        self.assertEquals(resp.status_code, 401)

        # Wrong auth token
        headers = dict(HTTP_HEADERS)
        headers['X-Auth-Token'] = 'wrong'
        resp = self.client.post(url, headers=headers.items())
        self.assertEquals(resp.status_code, 401)

        # Authorized
        resp = self.client.post(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue('user' in data)
        self.assertTrue(data['user'])
        self.assertEquals(data['user']['uid'], 'somebody')


class UserModelTests(BaseDbTestCase):
    """
    Tests of the authentication system.
    """

    AUTH_RETURN_VALUE = ('888', '999')
    INFO_RETURN_VALUE_1 = {
        'auth_user': {
            'uid': 'somebody',
            'first_name': 'Alexey',
            'last_name': 'Tolstoy',
            'mail': 'somenew@mail.com'
        },
        'user': {
            'id': 'somebody',
            'email': 'somenew@mail.com'
        }
    }
    INFO_RETURN_VALUE_3 = {
        'info': {
            'profile_url': 'http://profile1.com',
            'portrait_32_img': 'http://image.com/image1.jpg',
        }
    }
    INFO_RETURN_VALUE_2 = {
        'auth_user': {
            'uid': 'someother',
            'first_name': 'Fiodor',
            'last_name': 'Dostoevsky',
            'mail': 'someother@mail.com'
        },
        'user': {
            'id': 'someother',
            'email': 'someother@mail.com'
        }
    }
    INFO_RETURN_VALUE_4 = {
        'info': {
            'profile_url': 'http://profile2.com',
            'portrait_32_img': 'http://image.com/image2.jpg',
        }
    }

    @patch('api.accounts.auth.OdeskAuth.authenticate',
           Mock(return_value=AUTH_RETURN_VALUE))
    def test_authenticate(self):
        with patch('api.accounts.auth.OdeskAuth.get_my_info',
                   Mock(return_value=self.INFO_RETURN_VALUE_1)):
            with patch('api.accounts.auth.OdeskAuth.get_user_info',
                       Mock(return_value=self.INFO_RETURN_VALUE_3)):
                token, user = User.authenticate('123', '345', '567')
                self.assertTrue(token)
                self.assertEqual(user.uid, 'somebody')
                self.assertEqual(user.name, 'Alexey Tolstoy')
                self.assertEqual(user.email, 'somenew@mail.com')
                self.assertEqual(user.odesk_url, 'http://profile1.com')
                self.assertEqual(user.portrait_32_img,
                                 'http://image.com/image1.jpg')

        with patch('api.accounts.auth.OdeskAuth.get_my_info',
                   Mock(return_value=self.INFO_RETURN_VALUE_2)):
            with patch('api.accounts.auth.OdeskAuth.get_user_info',
                       Mock(return_value=self.INFO_RETURN_VALUE_4)):
                token, user = User.authenticate('123', '345', '567')
                self.assertTrue(token)
                self.assertTrue(str(user.id))
                self.assertEqual(user.uid, 'someother')
                self.assertEqual(user.name, 'Fiodor Dostoevsky')
                self.assertEqual(user.email, 'someother@mail.com')
                self.assertEqual(user.odesk_url, 'http://profile2.com')
                self.assertEqual(user.portrait_32_img,
                                 'http://image.com/image2.jpg')

    @patch('api.accounts.auth.OdeskAuth.get_auth_url',
           Mock(return_value='some_url'))
    def test_get_auth_url(self):
        self.assertEqual(User.get_auth_url(), 'some_url')


class OdeskAuthTests(TestCase):
    """
    Tests of the authentication system.
    """

    OAUTH_RESPONSE_TOKEN = ({
        'status': '200',
    }, 'oauth_callback_confirmed=1&oauth_token=123&oauth_token_secret=345')

    OAUTH_RESPONSE_ERROR = ({
        'status': '500',
    }, '')

    OAUTH_RESPONSE_ERROR_TOKEN = ({
        'status': '200',
    }, 'oauth_callback_confirmed=1')

    OAUTH_RESPONSE_ERROR_SECRET = ({
        'status': '200',
    }, 'oauth_callback_confirmed=1&oauth_token=789')

    OAUTH_RESPONSE_AUTH = ({
        'status': '200',
    }, 'oauth_callback_confirmed=1&oauth_token=789&oauth_token_secret=999')

    OAUTH_RESPONSE_INFO = ({
        'status': '200',
    }, '{"name": "Mickey"}')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_TOKEN))
    def test_odesk_auth_request_token(self):
        from api.accounts.auth import OdeskAuth
        auth = OdeskAuth()

        url, token, secret = auth.get_auth_url()
        self.assertEquals(
            url,
            'https://%s/services/api/auth?oauth_token=123' % UPWORK_URL
        )
        self.assertEquals(token, '123')
        self.assertEquals(secret, '345')

    def test_integration_odesk_auth_request_token(self):
        from api.accounts.auth import OdeskAuth
        auth = OdeskAuth()

        url, token, secret = auth.get_auth_url()
        self.assertTrue(
            '//%s/services/api/auth?oauth_token=' % UPWORK_URL in url,
            "Url is following: %s" % url
        )
        self.assertTrue(token)
        self.assertTrue(secret)

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_ERROR))
    def test_odesk_auth_request_response_error(self):
        from api.accounts.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.get_auth_url)

    @patch('oauth2.Client.request',
           Mock(return_value=OAUTH_RESPONSE_ERROR_TOKEN))
    def test_odesk_auth_request_token_error(self):
        from api.accounts.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.get_auth_url)

    @patch('oauth2.Client.request',
           Mock(return_value=OAUTH_RESPONSE_ERROR_SECRET))
    def test_odesk_auth_request_secret_error(self):
        from api.accounts.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.get_auth_url)

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_AUTH))
    def test_odesk_auth_authenticate(self):
        from api.accounts.auth import OdeskAuth
        auth = OdeskAuth()

        token, secret = auth.authenticate('123', '345', '567')
        self.assertEquals(token, '789')
        self.assertEquals(secret, '999')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_ERROR))
    def test_odesk_auth_authenticate_error(self):
        from api.accounts.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.authenticate,
                          '123', '345', '567')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_INFO))
    def test_odesk_auth_get_my_info(self):
        from api.accounts.auth import OdeskAuth
        auth = OdeskAuth()

        info = auth.get_my_info('123', '345', '567')
        self.assertEquals(info['name'], 'Mickey')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_INFO))
    def test_odesk_auth_get_user_info(self):
        from api.accounts.auth import OdeskAuth
        auth = OdeskAuth()

        info = auth.get_user_info('123', '345', '567')
        self.assertEquals(info['name'], 'Mickey')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_ERROR))
    def test_odesk_auth_get_my_info_error(self):
        from api.accounts.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.get_my_info,
                          '123', '345', '567')

    def test_stripOauthSignature(self):
        from api.accounts.auth import OAuthClient

        url = 'http://www.something.com'
        self.assertEqual(url, OAuthClient._stripOauthSignature(url))

        url = 'http://www.something.com?q=a'
        self.assertEqual(url, OAuthClient._stripOauthSignature(url))

        url = 'http://www.something.com?oauth_token=a'
        self.assertEqual(
            'http://www.something.com',
            OAuthClient._stripOauthSignature(url))
