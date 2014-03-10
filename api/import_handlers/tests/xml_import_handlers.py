# import httplib
# import json
# import os
# from mock import patch
# from moto import mock_s3

# from api.base.test_utils import BaseDbTestCase, TestChecksMixin, HTTP_HEADERS
# from ..views import ImportHandlerResource, DataSetResource
# from ..models import ImportHandler, DataSet
# from ..fixtures import ImportHandlerData, DataSetData
# from api.ml_models.fixtures import ModelData
# from api.ml_models.models import Model
# from api.model_tests.fixtures import TestResultData
# from api.model_tests.models import TestResult
# from api.features.fixtures import FeatureSetData, FeatureData


# class XmlImportHandlerTests(BaseDbTestCase, TestChecksMixin):
#     """
#     Tests of the XML ImportHandlers API.
#     """
#     BASE_URL = '/cloudml/importhandlers/'
#     RESOURCE = ImportHandlerResource
#     MODEL_NAME = ModelData.model_01.name
#     Model = ImportHandler
#     datasets = [ImportHandlerData, DataSetData, ModelData]

#     def setUp(self):
#         super(ImportHandlerTests, self).setUp()
#         self.obj = self.Model.query.filter_by(
#             name=ImportHandlerData.import_handler_01.name).first()

#     def test_list(self):
#         self.check_list(show='name')

#     def test_details(self):
#         resp = self.check_details(
#             show='name,type,import_params,data', obj=self.obj)
