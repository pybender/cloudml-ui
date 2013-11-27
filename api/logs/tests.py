import httplib
import json
import urllib

from api.logger import LogMessageHandler
from api.base.test_utils import BaseTestCase, HTTP_HEADERS
from views import LogResource
from models import LogMessage


class LogsTests(BaseTestCase):
    """
    Tests of the Statistics API.
    """
    BASE_URL = '/cloudml/logs/'
    RESOURCE = LogResource
    Model = LogMessage

    def setUp(self):
        super(LogsTests, self).setUp()
        self.Model.query.delete()

    def test_list(self):
        self._write_logs()
        resp = self.app.get(self.BASE_URL, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        items = json.loads(resp.data)['logs']
        self.assertEquals(len(items), 6)

    def test_filter(self):
        self._write_logs()
        url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
            'params.obj': '123',
            'show': 'level,type,content,params'
        }))
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        items = json.loads(resp.data)['logs']
        self.assertEquals(len(items), 6, "11111 %s" % items)

        scenario = [
            ('CRITICAL', 1, ('CRITICAL',)),
            ('ERROR', 2, ('ERROR', 'CRITICAL')),
            ('WARNING', 3, ('WARNING', 'ERROR', 'CRITICAL')),
            ('INFO', 4, ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
            ('DEBUG', 5, ('INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL')),
        ]

        for level, count, levels in scenario:
            url = '{0}?{1}'.format(self.BASE_URL, urllib.urlencode({
                'params.obj': '123',
                'show': 'level,type,content,params',
                'level': level
            }))
            resp = self.app.get(url, headers=HTTP_HEADERS)
            self.assertEquals(resp.status_code, httplib.OK, level)
            items = json.loads(resp.data)['logs']
            self.assertEquals(len(items), count, level)
            for lvl in levels:
                self.assertTrue(lvl in [item['level'] for item in items], level)

    def _write_logs(self):
        import logging
        logger = logging.getLogger('trainmodel_log')
        logger.handlers = []
        logger.addHandler(LogMessageHandler(
            log_type='trainmodel_log',
            params={
                'obj': '123'
            }
        ))
        logger.info('Info message')
        logger.debug('Debug message')
        logger.warning('Warn message')
        logger.error('Error message')
        logger.critical('Fatal message')
        logger.handlers = []
        logger.addHandler(LogMessageHandler(
            log_type='trainmodel_log',
            params={
                'obj': '124'
            }
        ))
        logger.info('Info message')
