from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from views import LogResource
from models import LogMessage


class LogsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Log Messages API.
    """
    BASE_URL = '/cloudml/logs/'
    RESOURCE = LogResource
    Model = LogMessage
    SHOW = 'level,type,content,params'

    def setUp(self):
        super(LogsTests, self).setUp()
        self.Model.query.delete()
        self._write_logs()

    def test_list(self):
        self.check_list(show=self.SHOW, count=6)

    def test_filter_by_type(self):
        self.check_list(
            show=self.SHOW,
            data={'type': 'runtest_log'},
            count=1)

    def test_filter_by_obj(self):
        self.check_list(
            show=self.SHOW,
            data={'params.obj': '123'},
            count=5)

    def test_filter_by_level(self):
        scenario = [
            ('CRITICAL', 1, ('CRITICAL',)),
            ('ERROR', 2, ('ERROR', 'CRITICAL')),
            ('WARNING', 3, ('WARNING', 'ERROR', 'CRITICAL')),
            ('INFO', 5, ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
            ('DEBUG', 6, ('INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL')),
        ]

        for level, count, levels in scenario:
            resp = self.check_list(
                show=self.SHOW,
                data={'level': level}, count=count)
            for lvl in levels:
                self.assertTrue(
                    lvl in [item['level'] for item in resp['logs']], level)

    def test_paging(self):
        for p in xrange(1, 4):
            self.check_list(
                show=self.SHOW,
                data={'params.obj': '123', 'page': p, 'per_page': 2},
                count=1 if p == 3 else 2)

    def _write_logs(self):
        import logging
        from api.logs.logger import LogMessageHandler
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
            log_type='runtest_log',
            params={
                'obj': '124'
            }
        ))
        logger.info('Info message')
