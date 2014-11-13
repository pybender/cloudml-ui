import uuid
import json
from datetime import datetime

from mock import patch, MagicMock
from moto import mock_s3
from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from api.import_handlers.views import ImportHandlerResource
from api.import_handlers.models import ImportHandler
from api.servers.fixtures import ServerData


class ImportHandlerResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the XML ImportHandlers API.
    """
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource
    Model = ImportHandler
    datasets = [ServerData]

    def setUp(self):
        super(ImportHandlerResourceTests, self).setUp()
        name = str(uuid.uuid1())
        with open('conf/extract.json', 'r') as fp:
            resp_data = self._check(method='post', data={
                'name': name,
                'data': fp.read()
            })
        self.assertEqual(resp_data[self.RESOURCE.OBJECT_NAME]['name'], name)
        self.obj = self.Model.query.filter_by(name=name).first()
        self.assertEqual(set(['start', 'end']), set(self.obj.import_params))

    def test_list(self):
        self.check_list(show='name,import_params')
