import json
from bson import ObjectId
from mock import patch, Mock

from api import app
from utils import BaseTestCase, HTTP_HEADERS


class AuthDecoratorsTests(BaseTestCase):
    """
    Tests of the authentication system.
    """

    def test_auth_decorators(self):
        from api.decorators import authenticate, public

        def _view(_argument):
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
        with app.test_request_context('/', headers=HTTP_HEADERS) as ctx:
            req = ctx.request

            view = authenticate(_view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample')
            self.assertEquals(res.status_code, 200)
            self.assertEquals(res.data, 'sample')
            self.assertEquals(str(req.user._id), '000000000000000000000111')
            self.assertEquals(str(req.user.uid), 'somebody')

        # Wrong auth token
        headers = dict(HTTP_HEADERS)
        headers['X-Auth-Token'] = 'wrong'
        with app.test_request_context('/', headers=headers.items()) as ctx:
            req = ctx.request

            view = authenticate(_view)
            self.assertEquals(view.__name__, _view.__name__)

            res = view('sample')
            self.assertEquals(res.status_code, 401)
            self.assertEquals(res.headers['X-Odesk-Error-Message'],
                              'Unauthorized')
            self.assertFalse(hasattr(req, 'user'))

        # Public view
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


class AuthResourceTests(BaseTestCase):
    """
    Tests of the authentication system.
    """

    BASE_URL = '/cloudml/auth'

    @patch('api.models.User.get_auth_url', return_value=('url', '1', '2'))
    def test_get_auth_url(self, mock_auth):
        url = '{0}/get_auth_url'.format(self.BASE_URL)
        resp = self.app.post(url, data={})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(mock_auth.call_count, 1)
        data = json.loads(resp.data)
        self.assertTrue('auth_url' in data)
        self.assertEquals(data['auth_url'], 'url')
        secret = app.db['auth_tokens'].find_one({'oauth_token': '1'})
        self.assertIsNotNone(secret)
        self.assertEquals(secret.get('oauth_token_secret'), '2')

    def test_authenticate(self):
        with patch(
            'api.models.User.authenticate',
            return_value=(
                '123',
                app.db.User.find_one({
                    '_id': ObjectId('000000000000000000000111')})
            )
        ) as mock_auth:

            url = '{0}/authenticate?oauth_token={1}&oauth_verifier={2}'.format(
                self.BASE_URL, '123', '345'
            )

            # Wrong token
            resp = self.app.post(url, data={})
            self.assertEquals(resp.status_code, 500)
            self.assertEquals(resp.headers['X-Odesk-Error-Message'],
                              'Wrong token: 123')

            # Proper token
            app.db['auth_tokens'].insert({
                'oauth_token': '123',
                'oauth_token_secret': '999',
            })

            resp = self.app.post(url, data={})
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
        resp = self.app.post(url)
        self.assertEquals(resp.status_code, 401)

        # Wrong auth token
        headers = dict(HTTP_HEADERS)
        headers['X-Auth-Token'] = 'wrong'
        resp = self.app.post(url, headers=headers.items())
        self.assertEquals(resp.status_code, 401)

        # Authorized
        resp = self.app.post(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue('user' in data)
        self.assertTrue(data['user'])
        self.assertEquals(data['user']['uid'], 'somebody')


class UserModelTests(BaseTestCase):
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
        'info': {
            'profile_url': 'http://profile2.com',
            'portrait_32_img': 'http://image.com/image2.jpg',
        }
    }

    @patch('api.auth.OdeskAuth.authenticate', Mock(return_value=AUTH_RETURN_VALUE))
    def test_authenticate(self):
        with patch('api.auth.OdeskAuth.get_my_info',
                   Mock(return_value=self.INFO_RETURN_VALUE_1)):
            token, user = app.db.User.authenticate('123', '345', '567')
            self.assertTrue(token)
            self.assertEqual(str(user._id), '000000000000000000000111')
            self.assertEqual(user.uid, 'somebody')
            self.assertEqual(user.name, 'Alexey Tolstoy')
            self.assertEqual(user.email, 'somenew@mail.com')
            self.assertEqual(user.odesk_url, 'http://profile1.com')
            self.assertEqual(user.portrait_32_img, 'http://image.com/image1.jpg')

        with patch('api.auth.OdeskAuth.get_my_info',
                   Mock(return_value=self.INFO_RETURN_VALUE_2)):
            token, user = app.db.User.authenticate('123', '345', '567')
            self.assertTrue(token)
            self.assertTrue(str(user._id))
            self.assertNotEqual(str(user._id), '000000000000000000000111')
            self.assertEqual(user.uid, 'someother')
            self.assertEqual(user.name, 'Fiodor Dostoevsky')
            self.assertEqual(user.email, 'someother@mail.com')
            self.assertEqual(user.odesk_url, 'http://profile2.com')
            self.assertEqual(user.portrait_32_img, 'http://image.com/image2.jpg')


class OdeskAuthTests(BaseTestCase):
    """
    Tests of the authentication system.
    """

    OAUTH_RESPONSE_TOKEN = ({
        'status': '200',
    }, 'oauth_callback_confirmed=1&oauth_token=123&oauth_token_secret=345')

    OAUTH_RESPONSE_ERROR = ({
        'status': '500',
    }, '')

    OAUTH_RESPONSE_AUTH = ({
        'status': '200',
    }, 'oauth_callback_confirmed=1&oauth_token=789&oauth_token_secret=999')

    OAUTH_RESPONSE_INFO = ({
        'status': '200',
    }, '{"name": "Mickey"}')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_TOKEN))
    def test_odesk_auth_request_token(self):
        from api.auth import OdeskAuth
        auth = OdeskAuth()

        url, token, secret = auth.get_auth_url()
        self.assertEquals(
            url,
            'https://www.odesk.com/services/api/auth?oauth_token=123'
        )
        self.assertEquals(token, '123')
        self.assertEquals(secret, '345')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_ERROR))
    def test_odesk_auth_request_token_error(self):
        from api.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.get_auth_url)

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_AUTH))
    def test_odesk_auth_authenticate(self):
        from api.auth import OdeskAuth
        auth = OdeskAuth()

        token, secret = auth.authenticate('123', '345', '567')
        self.assertEquals(token, '789')
        self.assertEquals(secret, '999')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_ERROR))
    def test_odesk_auth_authenticate_error(self):
        from api.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.authenticate,
                          '123', '345', '567')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_INFO))
    def test_odesk_auth_get_my_info(self):
        from api.auth import OdeskAuth
        auth = OdeskAuth()

        info = auth.get_my_info('123', '345', '567')
        self.assertEquals(info['name'], 'Mickey')

    @patch('oauth2.Client.request', Mock(return_value=OAUTH_RESPONSE_ERROR))
    def test_odesk_auth_get_my_info_error(self):
        from api.auth import OdeskAuth, AuthException
        auth = OdeskAuth()
        self.assertRaises(AuthException, auth.get_my_info,
                          '123', '345', '567')
