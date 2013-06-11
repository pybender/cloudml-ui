import httplib
import json
from bson.objectid import ObjectId

from utils import BaseTestCase
from api.views import ImportHandlerResource


class ImportHandlersTests(BaseTestCase):
    """
    Tests of the ImportHandlers API.
    """
    HANDLER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('datasets.json', 'importhandlers.json', )
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource

    def setUp(self):
        super(ImportHandlersTests, self).setUp()
        self.Model = self.db.ImportHandler
        self.obj = self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)})

    def test_list(self):
        self._check_list()

    def test_edit_name(self):
        url = self._get_url(id=self.obj._id)
        data = {'name': 'new name'}
        resp = self.app.put(url, data=data)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        handler = self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)})
        self.assertEquals(handler.name, data['name'])

    def test_delete(self):
        datasets = self.db.DataSet.find({'import_handler_id': self.HANDLER_ID})
        self.assertTrue(datasets.count(), 'Invalid fixtures')

        url = self._get_url(id=self.obj._id)
        resp = self.app.delete(url)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertFalse(self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)}))
        datasets = self.db.DataSet.find({'import_handler_id': self.HANDLER_ID})
        self.assertFalse(datasets.count(), 'DataSets should be removed')


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