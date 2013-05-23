import httplib
import json

from utils import BaseTestCase
from api.views import ImportHandlerResource


class ImportHandlersTests(BaseTestCase):
    """
    Tests of the ImportHandlers API.
    """
    HANDLER_NAME = 'IH1'
    FIXTURES = ('importhandlers.json', )
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource

    def setUp(self):
        super(ImportHandlersTests, self).setUp()
        self.Model = self.db.ImportHandler
        self.obj = self.Model.find_one({'name': self.HANDLER_NAME})

    def test_list(self):
        self._check_list()
