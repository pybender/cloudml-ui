import httplib
import json
import urllib

from api import app
from api.base.test_utils import BaseMongoTestCase, TestChecksMixin, \
    HTTP_HEADERS, BaseDbTestCase
from api.logs.views import LogResource

# TODO: uncomment and fix
# class LogsTests(BaseMongoTestCase, TestChecksMixin, BaseDbTestCase):
#     """
#     Tests of the Statistics API.
#     """
#     BASE_URL = '/cloudml/logs/'
#     RESOURCE = LogResource
#
#     def setUp(self):
#         BaseDbTestCase.setUp(self)
#         BaseMongoTestCase.setUp(self)
#         self.Model = app.db.LogMessage
#         self.Model.collection.remove()
#
#     def test_list(self):
#         import logging
#         from logger import LogMessageHandler
#         logger = logging.getLogger('testing')
#         logger.handlers = []
#         logger.addHandler(LogMessageHandler(
#             log_type='testing',
#             params={
#                 'obj': 123
#             }
#         ))
#         logger.addHandler(LogMessageHandler(
#             log_type='testing',
#             params={
#                 'obj': 124
#             }
#         ))
#         logger.info('Info message')
#         logger.debug('Debug message')
#         logger.warning('Warn message')
#         logger.error('Error message')
#         logger.critical('Fatal message')
#
#         # url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
#         #     'params.obj': '123',
#         #     'show': 'level,type,content,params'
#         # }))
#         # resp = self.client.get(url, headers=HTTP_HEADERS)
#         # self.assertEquals(resp.status_code, httplib.OK)
#         # items = json.loads(resp.data)['logs']
#         # self.assertEquals(len(items), 5)
#
#
#         scenario = [
#             ('CRITICAL', 1, ('CRITICAL',)),
#             ('ERROR', 2, ('ERROR', 'CRITICAL')),
#             ('WARNING', 3, ('WARNING', 'ERROR', 'CRITICAL')),
#             ('INFO', 4, ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
#             ('DEBUG', 5, ('INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL')),
#         ]
#
#         for level, count, levels in scenario:
#             url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
#                 'params.obj': '123',
#                 'show': 'level,type,content,params',
#                 'level': level
#             }))
#             resp = self.client.get(url, headers=HTTP_HEADERS)
#             self.assertEquals(resp.status_code, httplib.OK, level)
#             print resp.data
#             items = json.loads(resp.data)['logs']
#             print "l", len(items), count, level
#             self.assertEquals(len(items), count, level)
#             for lvl in levels:
#                 self.assertTrue(
#                     lvl in [item['level'] for item in items], level)
