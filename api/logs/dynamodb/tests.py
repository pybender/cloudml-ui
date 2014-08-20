import httplib
import json
import urllib
from moto import mock_dynamodb2

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from api.logs.views import LogResource


class LogsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Statistics API.
    """
    BASE_URL = '/cloudml/logs/'
    RESOURCE = LogResource

    OBJECT_ID = -1

    def setUp(self):
        BaseDbTestCase.setUp(self)
        from models import LogMessage
        self.dynamodb_mock = mock_dynamodb2()
        self.dynamodb_mock.start()
        LogMessage.create_table()

    def tearDown(self):
        BaseDbTestCase.tearDown(self)
        self.dynamodb_mock.stop()

    def test_list(self):
        import logging
        from logger import LogMessageHandler

        logger = logging.getLogger('testing')
        logger.handlers = []
        logger.addHandler(LogMessageHandler(
            log_type='testing',
            params={
                'obj': self.OBJECT_ID
            }
        ))
        logger.info('Info message')
        logger.debug('Debug message')
        logger.warning('Warn message')
        logger.error('Error message')
        logger.critical('Fatal message')

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            # 'next_token': None,
            'object_id': self.OBJECT_ID,
            'type': 'testing',
            # 'per_page': 20
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        items = json.loads(resp.data)['logs']

        self.assertEquals(len(items), 5)

        scenario = [
            ('CRITICAL', 1, ('CRITICAL',)),
            ('ERROR', 2, ('ERROR', 'CRITICAL')),
            ('WARNING', 3, ('WARNING', 'ERROR', 'CRITICAL')),
            ('INFO', 4, ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
            ('DEBUG', 5, ('INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL')),
        ]

        for level, count, levels in scenario:
            url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
                'next_token': None,
                'object_id': self.OBJECT_ID,
                'type': 'testing',
                'per_page': 20,
                'level': level
            }))
            resp = self.client.get(url, headers=HTTP_HEADERS)
            self.assertEquals(resp.status_code, httplib.OK, level)
            items = json.loads(resp.data)['logs']
            self.assertEquals(len(items), count, level)
            for lvl in levels:
                self.assertTrue(
                    lvl in [item['level'] for item in items], level)
