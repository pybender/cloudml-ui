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

    def test_put(self):
        data = {"name": "new name", "target_schema": "new-schema"}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(obj.name, data['name'])
        self.assertEquals(obj.target_schema, data['target_schema'])

        data = {'queries.-1.name': 'new query',
                'queries.-1.sql': 'select * from ...'}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(len(obj.queries), 2, "Query should be added")
        query = obj.queries[1]
        self.assertEquals(query['name'], 'new query')
        self.assertEquals(query['sql'], 'select * from ...')

        data = {'queries.1.name': 'new query1',
                'queries.1.sql': 'select * from t1...'}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(len(obj.queries), 2, "Query should be updated")
        query = obj.queries[1]
        self.assertEquals(query['name'], 'new query1')
        self.assertEquals(query['sql'], 'select * from t1...')

        data = {'queries.1.items.-1.source': 'some-source'}
        resp, obj = self._check_put(data, load_model=True)
        self.assertEquals(len(obj.queries[1]['items']), 1,
                          "Item should be updated")
        item = obj.queries[1]['items'][0]
        self.assertEquals(item['source'], 'some-source')

        data = {'queries.1.items.0.source': 'other-source'}
        resp, obj = self._check_put(data, load_model=True)
        item = obj.queries[1]['items'][0]
        self.assertEquals(item['source'], 'other-source')

        data = {'queries.1.items.0.target_features.-1.name': 'hire_outcome'}
        resp, obj = self._check_put(data, load_model=True)
        features = obj.queries[1]['items'][0]['target_features']
        self.assertEquals(len(features), 1,
                          "Item should be updated")
        feature = features[0]
        self.assertEquals(feature['name'], 'hire_outcome')

        data = {'queries.1.items.0.target_features.0.name': 'hire_outcome2'}
        resp, obj = self._check_put(data, load_model=True)
        feature = obj.queries[1]['items'][0]['target_features'][0]
        self.assertEquals(feature['name'], 'hire_outcome2')

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
        self.assertIsNone(self.Model.find_one(
            {'_id': ObjectId(self.HANDLER_ID)}))

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
