import httplib
from bson.objectid import ObjectId

from utils import BaseTestCase, HTTP_HEADERS
from api.views import ImportHandlerResource


class ImportHandlersTests(BaseTestCase):
    """
    Tests of the ImportHandlers API.
    """
    HANDLER_ID = '5170dd3a106a6c1631000000'
    FIXTURES = ('models.json', 'datasets.json', 'importhandlers.json', )
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource
    MODEL_NAME = 'TrainedModel'

    def setUp(self):
        super(ImportHandlersTests, self).setUp()
        self.Model = self.db.ImportHandler
        self.obj = self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)})

    def test_list(self):
        self._check_list()

    def test_edit_name(self):
        url = self._get_url(id=self.obj._id)
        data = {'name': 'new name'}
        resp = self.app.put(url, data=data, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertTrue(self.RESOURCE.OBJECT_NAME in resp.data)
        handler = self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)})
        self.assertEquals(handler.name, data['name'])

    def test_delete(self):
        datasets = self.db.DataSet.find({'import_handler_id': self.HANDLER_ID})
        self.assertTrue(datasets.count(), 'Invalid fixtures')
        import shutil
        files = []
        for dataset in datasets:
            files.append(dataset.filename)
            shutil.copy2(dataset.filename, dataset.filename + '.bak')

        model = self.db.Model.find_one({'name': self.MODEL_NAME})
        model.test_import_handler = self.obj
        model.train_import_handler = self.obj
        model.save()

        url = self._get_url(id=self.obj._id)
        resp = self.app.delete(url, headers=HTTP_HEADERS)

        self.assertEquals(resp.status_code, httplib.NO_CONTENT)
        self.assertIsNone(self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)}))

        datasets = self.db.DataSet.find({'import_handler_id': self.HANDLER_ID})
        self.assertFalse(datasets.count(), 'DataSets should be removed')
        for filename in files:
            shutil.move(filename + '.bak', filename)

        model = self.db.Model.find_one({'name': self.MODEL_NAME})
        self.assertIsNone(model.test_import_handler, 'Ref should be removed')
        self.assertIsNone(model.train_import_handler, 'Ref should be removed')

    def test_download(self):
        url = self._get_url(id=self.obj._id, action='download')
        resp = self.app.get(url, headers=HTTP_HEADERS)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(resp.mimetype, 'text/plain')
        self.assertEquals(resp.headers['Content-Disposition'],
                          'attachment; filename=importhandler-%s.json' %
                          self.obj.name)


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