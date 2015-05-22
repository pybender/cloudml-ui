import httplib
import json
import urllib
from moto import mock_dynamodb2

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from api.logs.views import LogResource


class LogsTests(BaseDbTestCase, TestChecksMixin):
    """
    moto (currently v0.3.3), doesn't implement query filter for dynamodb2
    we can only run against memory db for now
    https://github.com/spulec/moto/issues/164
    """
    BASE_URL = '/cloudml/logs/'
    RESOURCE = LogResource

    OBJECT_ID = -1

    def _delete_table(self):
        """
        No need for this when moto supports query filter
        :return:
        """
        from api import app
        from models import LogMessage
        if app.config.get('TEST_MODE') or app.config.get('LOCAL_DYNAMODB'):
            from api.amazon_utils import AmazonDynamoDBHelper
            db = AmazonDynamoDBHelper()
            try:
                db.conn.delete_table(LogMessage.TABLE_NAME)
            except:
                pass

    def setUp(self):
        BaseDbTestCase.setUp(self)
        self._delete_table()
        from models import LogMessage
        # TODO: uncomment the following when moto implements query filter
        # self.dynamodb_mock = mock_dynamodb2()
        # self.dynamodb_mock.start()
        LogMessage.create_table()
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
        logger.info('1. Info message')
        logger.debug('2. Debug message')
        logger.warning('3. Warn message')
        logger.error('4. Error message')
        logger.critical('5. Fatal message')

    def tearDown(self):
        BaseDbTestCase.tearDown(self)
        self._delete_table()
        # TODO: uncomment the following when moto implements query filter,
        # and remove the delete table logic
        # self.dynamodb_mock.stop()

    # TODO: enable this test when moto supports query filters
    def xtest_list_with_levels(self):
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
                # 'next_token': None,
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

    # TODO: enable this test when moto supports query filters
    def xtest_list_with_next_page(self):
        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'object_id': self.OBJECT_ID,
            'type': 'testing',
            'per_page': 2
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        json_data = json.loads(resp.data)
        items = json_data['logs']

        self.assertEquals(len(items), 2)
        self.assertEqual(items[0]['content'], '1. Info message')
        self.assertEqual(items[1]['content'], '2. Debug message')

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'object_id': self.OBJECT_ID,
            'type': 'testing',
            'per_page': 2,
            'next_token': json_data['next_token']
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        json_data = json.loads(resp.data)
        items = json_data['logs']

        self.assertEquals(len(items), 2)
        self.assertEqual(items[0]['content'], '3. Warn message')
        self.assertEqual(items[1]['content'], '4. Error message')

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'object_id': self.OBJECT_ID,
            'type': 'testing',
            'per_page': 2,
            'next_token': json_data['next_token']
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        json_data = json.loads(resp.data)
        items = json_data['logs']

        self.assertEquals(len(items), 1)
        self.assertEqual(items[0]['content'], '5. Fatal message')
        self.assertIsNone(json_data['next_token'])

    # TODO: enable this test when moto supports query filters
    def xtest_list_with_ordering(self):
        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'object_id': self.OBJECT_ID,
            'type': 'testing'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        json_data = json.loads(resp.data)
        items = json_data['logs']

        self.assertEqual(5, len(items))
        self.assertEqual(items[0]['content'], '1. Info message')
        self.assertEqual(items[1]['content'], '2. Debug message')
        self.assertEqual(items[2]['content'], '3. Warn message')
        self.assertEqual(items[3]['content'], '4. Error message')
        self.assertEqual(items[4]['content'], '5. Fatal message')

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'object_id': self.OBJECT_ID,
            'type': 'testing',
            'order': 'asc'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        json_data = json.loads(resp.data)
        items = json_data['logs']

        self.assertEqual(5, len(items))
        self.assertEqual(items[0]['content'], '1. Info message')
        self.assertEqual(items[1]['content'], '2. Debug message')
        self.assertEqual(items[2]['content'], '3. Warn message')
        self.assertEqual(items[3]['content'], '4. Error message')
        self.assertEqual(items[4]['content'], '5. Fatal message')

        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'object_id': self.OBJECT_ID,
            'type': 'testing',
            'order': 'zinger'
        }))
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        json_data = json.loads(resp.data)
        items = json_data['logs']

        self.assertEqual(5, len(items))
        self.assertEqual(items[0]['content'], '5. Fatal message')
        self.assertEqual(items[1]['content'], '4. Error message')
        self.assertEqual(items[2]['content'], '3. Warn message')
        self.assertEqual(items[3]['content'], '2. Debug message')
        self.assertEqual(items[4]['content'], '1. Info message')

    def xtest_bad_next_token(self):
        url = '{0}?{1}'.format(self.BASE_URL, 'level=WARNING&next_token=&object_id=69&order=desc&per_page=20&show=level%2Ctype%2Ccontent%2Cparams%2Ccreated_on&sort_by=created_on&type=importdata_log')
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
