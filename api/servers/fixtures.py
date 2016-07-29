from fixture import DataSet
from api.ml_models.fixtures import ModelData
from api.model_tests.fixtures import TestResultData, TestExampleData


class ServerData(DataSet):
    class server_01:
        name = 'analytics'
        ip = '127.0.0.1'
        folder = 'odesk-match-cloudml/analytics'
        is_default = True

    class server_02:
        name = 'local'
        ip = '127.0.0.2'
        folder = 'odesk-match-cloudml/local'
        is_default = True


class ServerModelVerificationData(DataSet):
    class model_verification_01:
        status = 'New'
        model = ModelData.model_01
        test_result = TestResultData.test_01
        server = ServerData.server_01
        params_map = {"application": "opening_id",
                      "country": "employer.country"}
        error = ""
        description = {
            'import_handler_metadata': {
                'name': 'my_import_handler'
            }}


class VerificationExampleData(DataSet):
    class verification_example_01:
        example = TestExampleData.test_example_01
        verification = ServerModelVerificationData.model_verification_01
        result = {
            "data": {
                'opening_id': "201913099",
                'employer->country': 'USA',
                'contractor->dev_blurb': "Over ten years experience "
                                         "successfully performing a number of "
                                         "data entry and clerical tasks."
            }
        }
