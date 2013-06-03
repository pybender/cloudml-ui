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



#     def test_post_with_invalid_import_handler(self):
#         features = open('./conf/features.json', 'r').read()
#         post_data = {'importhandler': 'smth',
#                      'features': features,
#                      'name': 'new'}
#         self._checkValidationErrors(self.BASE_URL, post_data,
#                                     'Invalid importhandler: smth \
# No JSON object could be decoded')

#         features = open('./conf/features.json', 'r').read()
#         post_data = {'importhandler': '{}',
#                      'features': features,
#                      'name': 'new'}
#         self._checkValidationErrors(self.BASE_URL, post_data,
#                                     'importhandler is required')