import httplib
import json
import urllib
from mock import patch, MagicMock, ANY

from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
from api.logs.views import LogResource
from models import LogMessage

class LogsTests(BaseDbTestCase, TestChecksMixin):
    BASE_URL = '/cloudml/logs/'
    RESOURCE = LogResource

    OBJECT_ID = -1

    def setUp(self):
        BaseDbTestCase.setUp(self)
        import logging
        from logger import LogMessageHandler

        self.logger = logging.getLogger('testing')
        self.logger.handlers = []
        self.logger.addHandler(LogMessageHandler(
            log_type='testing',
            params={
                'obj': self.OBJECT_ID
            }
        ))

    def tearDown(self):
        BaseDbTestCase.tearDown(self)

    @patch('api.amazon_utils.AmazonDynamoDBHelper.create_table')
    def test_create_table(self, create_table_mock):
        LogMessage.create_table()
        create_table_mock.assert_called_with(LogMessage.TABLE_NAME,
                                             LogMessage.SCHEMA,
                                             LogMessage.SCHEMA_TYPES)

    def test_to_dict(self):
        log = LogMessage('trainmodel_log', 'log text', 25)
        log_dict = log.to_dict()
        self.assertTrue(isinstance(log_dict, dict))
        self.assertIn('created_on', log_dict)
        self.assertEqual(log_dict['object_id'], 25)
        self.assertEqual(log_dict['type'], 'trainmodel_log')
        self.assertIn('trainmodel_log:', log_dict['id'])
        self.assertEqual(4, log_dict['level'])

    @patch('api.amazon_utils.AmazonDynamoDBHelper.put_item')
    def test_save(self, put_item_mock):
        self.logger.info("1. Info message")
        put_item_mock.assert_called_with(LogMessage.TABLE_NAME,
                                         {'id': ANY,
                                          'type': 'testing',
                                          'content': '1. Info message',
                                          'object_id': self.OBJECT_ID,
                                          'level': 4,
                                          'created_on': ANY})

    @patch('api.amazon_utils.AmazonDynamoDBHelper.delete_items')
    def test_delete_related_logs(self, delete_mock):
        from api import app
        app.config['TEST_MODE'] = False
        LogMessage.delete_related_logs(self.OBJECT_ID)
        delete_mock.assert_called_with(
            LogMessage.TABLE_NAME, KeyConditionExpression=ANY,
            keys=['id', 'object_id'])
        expr = delete_mock.call_args[1]['KeyConditionExpression']\
            .get_expression()
        self.assertEqual(expr['operator'], '=')
        self.assertEqual(expr['values'][0].name, 'object_id')
        self.assertEqual(expr['values'][1], self.OBJECT_ID)

        # in test mode
        app.config['TEST_MODE'] = True
        LogMessage.delete_related_logs(self.OBJECT_ID)
        delete_mock.assert_not_called()

    @patch('time.mktime')
    @patch('api.amazon_utils.AmazonDynamoDBHelper.get_items')
    def test_filter_by_object(self, query_mock, dt_now):
        dt_now.return_value = 1458214261.0
        scenarios = [
            {
                'request': {'object_id': self.OBJECT_ID,
                            'type': 'testing',
                            'per_page': 20,
                            'level': 'ERROR'},
                'query': {
                    'KeyConditionExpression': {
                        'operator': 'AND',
                        'values': [
                            {'operator': '=',
                             'values': ['object_id', self.OBJECT_ID]},
                            {'operator': '>',
                             'values': ['id', 'testing:0']}
                        ]
                    },
                    'Limit': 20,
                    'ScanIndexForward': True,
                    'FilterExpression': {'operator': '<=',
                                         'values': ['level', 1]}
                },
                'result': {'items': [], 'items_from_mock': [],
                           'next_token': None
                }
            },
            {
                'request': {'object_id': self.OBJECT_ID,
                            'type': 'testing',
                            'per_page': 2,
                            'level': 'INFO',
                            'next_token': '1234567889.35',
                            'order': 'desc'},
                'query': {
                    'KeyConditionExpression': {
                        'operator': 'AND',
                        'values': [
                            {'operator': '=',
                             'values': ['object_id', self.OBJECT_ID]},
                            {'operator': '<',
                             'values': ['id', 'testing:1234567889.35']}
                        ]
                    },
                    'Limit': 2,
                    'ScanIndexForward': False,
                    'FilterExpression': {'operator': '<=',
                                         'values': ['level', 4]}
                },
                'result': {
                    'items_from_mock': [
                        {'created_on': "1245688889.12", 'level': '4'},
                        {'created_on': "1245678889.12", 'level': '3'}
                    ],
                    'items': [
                        {'created_on': "2009-06-22 19:41:29.120000",
                         'level': 'INFO'},
                        {'created_on': "2009-06-22 16:54:49.120000",
                         'level': 'WARNING'}
                    ],
                    'next_token': "1245678889.12"
                }
            },
            {
                'request': {'object_id': self.OBJECT_ID,
                            'type': 'testing',
                            'level': 'DEBUG',
                            'per_page': 10,
                            'next_token': '1234567889.35',
                            'order': 'asc'},
                'query': {
                    'KeyConditionExpression': {
                        'operator': 'AND',
                        'values': [
                            {'operator': '=',
                             'values': ['object_id', self.OBJECT_ID]},
                            {'operator': '>',
                             'values': ['id', 'testing:1234567889.35']}
                        ]
                    },
                    'Limit': 10,
                    'ScanIndexForward': True,
                    'FilterExpression': {'operator': '<=',
                                         'values': ['level', 5]}
                },
                'result': {
                    'items_from_mock': [
                        {'created_on': "1245688889.12", 'level': '5'}
                    ],
                    'items': [
                        {'created_on': "2009-06-22 19:41:29.120000",
                         'level': 'DEBUG'}
                    ],
                    'next_token': None
                }
            },
            {
                'request': {'object_id': self.OBJECT_ID,
                            'type': 'testing',
                            'order': 'desc'},
                'query': {
                    'KeyConditionExpression': {
                        'operator': 'AND',
                        'values': [
                            {'operator': '=',
                             'values': ['object_id', self.OBJECT_ID]},
                            {'operator': '<',
                             'values': ['id', 'testing:1458214261.0']}
                        ]
                    },
                    'ScanIndexForward': False
                },
                'result': {
                    'items_from_mock': [
                        {'created_on': "1144568889.12", 'level': '5'},
                        {'created_on': "1144567889.12", 'level': '5'}
                    ],
                    'items': [
                        {'created_on': "2006-04-09 10:48:09.120000",
                         'level': 'DEBUG'},
                        {'created_on': "2006-04-09 10:31:29.120000",
                         'level': 'DEBUG'}
                    ],
                    'next_token': "1144567889.12"
                }
            }
        ]

        for sc in scenarios:
            query_mock.return_value = sc['result']['items_from_mock']
            url = '{0}?{1}'.format(self.BASE_URL,
                                   urllib.urlencode(sc['request']))
            resp = self.client.get(url, headers=HTTP_HEADERS)
            kwargs = {}
            for key, val in sc['query'].iteritems():
                kwargs[key] = ANY if isinstance(val, dict) else val

            query_mock.assert_called_with(LogMessage.TABLE_NAME, **kwargs)

            # check Key Condition
            expr = query_mock.call_args[1]['KeyConditionExpression']\
                .get_expression()
            self.assertEqual(sc['query']['KeyConditionExpression']['operator'],
                             expr['operator'])
            values = sc['query']['KeyConditionExpression']['values']
            for i in range(len(values)):
                expr_i = expr['values'][i].get_expression()
                self.assertEqual(values[i]['operator'], expr_i['operator'])
                self.assertEqual(values[i]['values'][0],
                                 expr_i['values'][0].name)
                self.assertEqual(values[i]['values'][1], expr_i['values'][1])

            # check Filter Expression if any
            if 'FilterExpression' in sc['query']:
                expr = query_mock.call_args[1]['FilterExpression']\
                    .get_expression()
                self.assertEqual(
                    sc['query']['FilterExpression']['operator'],
                    expr['operator'])
                values = sc['query']['FilterExpression']['values']
                self.assertEqual(values[0], expr['values'][0].name)
                self.assertEqual(values[1], expr['values'][1])

            self.assertEquals(resp.status_code, httplib.OK)
            items = json.loads(resp.data)['logs']
            next_token = json.loads(resp.data)['next_token']
            self.assertEqual(sc['result']['items'], items)
            self.assertEqual(sc['result']['next_token'], next_token)


    # TODO: enable this test when checking query filters is possible
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

    # TODO: enable this test when checking query filters is possible
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

    # TODO: enable this test when checking query filters is possible
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

    @patch('api.amazon_utils.AmazonDynamoDBHelper._get_table')
    def test_bad_next_token(self, table_mock):
        table = MagicMock()
        table.query.return_value = {"Items": []}
        table_mock.return_value = table

        url = '{0}?{1}'.format(
            self.BASE_URL,
            "level=WARNING&next_token=&object_id=69&order=desc&per_page=20"
            "&show=level%2Ctype%2Ccontent%2Ccreated_on&sort_by=created_on"
            "&type=importdata_log")
        resp = self.client.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
