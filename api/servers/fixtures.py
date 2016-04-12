from fixture import DataSet
from api.ml_models.fixtures import ModelData
from api.model_tests.fixtures import TestResultData


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
        params_map = {"application": "app"}
        error = ""
        description = {
            'import_handler_metadata': {
                'name': 'my_import_handler'
            }}
