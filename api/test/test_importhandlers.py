import httplib
import json

from utils import BaseTestCase
from api.utils import ERR_INVALID_DATA


class ImportHandlersTests(BaseTestCase):
    """
    Tests of the ImportHandlers API.
    """
    HANDLER_NAME = 'IH1'
    FIXTURES = ('importhandlers.json', )
    BASE_URL = '/cloudml/importhandlers/'

    def setUp(self):
        super(ImportHandlersTests, self).setUp()
        self.handler = self.db.ImportHandler.find_one({'name': self.HANDLER_NAME})

    def test_list(self):
        resp = self.app.get(self.BASE_URL)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        self.assertTrue('import_handlers' in data, data)
        import_handlers_resp = data['import_handlers']
        count = self.db.ImportHandler.find().count()
        self.assertEquals(count, len(data['import_handlers']))
        self.assertEquals(import_handlers_resp[0].keys(), [u'_id', u'name'])

        url = self._get_url(show='created_on,type')
        resp = self.app.get(url)
        self.assertEquals(resp.status_code, httplib.OK)
        data = json.loads(resp.data)
        import_handlers_resp = data['import_handlers']
        self.assertEquals(import_handlers_resp[0].keys(),
                          [u'created_on', u'_id', u'type'])
