from fixture import DataSet

from api.ml_models.fixtures import ModelData
from api.import_handlers.fixtures import DataSetData


class TestData(DataSet):
    class test_01:
        name = "Test-1"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "TrainedModel"
        model_id = ModelData.model_01.ref('id')
        dataset_id = DataSetData.dataset_01.ref('id')
        parameters = {}
        metrics = {}
        examples_count = 100
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        classes_set = []
        accuracy = 0.95

    class test_02:
        name = "Test-2"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "TrainedModel"
        parameters = {}
        metrics = {}
        examples_count = 100
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        model_id = ModelData.model_01.ref('id')
        dataset_id = DataSetData.dataset_01.ref('id')
        classes_set = []
        accuracy = 0.95

    class test_03:
        name = "Test-3"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "OtherModel"
        parameters = {}
        metrics = {}
        examples_count = 100
        examples_fields = ["hire_outcome", "application_id"]
        model_id = ModelData.model_01.ref('id')
        dataset_id = DataSetData.dataset_01.ref('id')
        error = ""
        data = {}
        classes_set = []
        accuracy = 0.95

    class test_04:
        name = "Test-4"
        status = "Queued"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "TrainedModel"
        parameters = {}
        metrics = {}
        examples_count = 0
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        model_id = ModelData.model_01.ref('id')
        dataset_id = DataSetData.dataset_01.ref('id')
        classes_set = []
        accuracy = 0


class TestExampleData(DataSet):
    class test_example_01:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-1"
        pred_label = "0"
        label = "1"
        test_name = "Test-1"
        model_name = "TrainedModel"
        data_input = {}
        test_id = "000000000000000000000002"
        weighted_data_input = {}
        prob = [0.123, 0.5]
        example_id = "1"
        num = 0
        model_id = ModelData.model_01.ref('id')
        test_id = TestData.test_01.ref('id')

    class test_example_02:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-2"
        pred_label = "1"
        label = "1"
        test_name = "Test-1"
        model_name = "TrainedModel"
        data_input = {}
        test_id = None
        weighted_data_input = {}
        prob = [0.123, 0.5]
        example_id = "1a"
        num = 1
        model_id = ModelData.model_01.ref('id')
        test_id = TestData.test_01.ref('id')

    class test_example_03:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-3"
        pred_label = "1"
        label = "0"
        test_name = "Test-1"
        model_name = "TrainedModel"
        data_input = {}
        test_id = None
        weighted_data_input = {}
        prob = [0.123, 0.5]
        example_id = "2"
        num = 3
        model_id = ModelData.model_01.ref('id')
        test_id = TestData.test_01.ref('id')

    class test_example_04:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #2-3"
        pred_label = "1"
        label = "0"
        test_name = "Test-2"
        model_name = "TrainedModel"
        data_input = {}
        weighted_data_input = {}
        prob = [0.123, 0.5]
        example_id = "3"
        on_s3 = True
        num = 0
        model_id = ModelData.model_01.ref('id')
        test_id = TestData.test_01.ref('id')

    class test_example_05:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some OtherModel Example #1-1"
        pred_label = "1"
        label = "0"
        test_name = "Test-1"
        model_name = "OtherModel"
        data_input = {}
        weighted_data_input = {}
        prob = [0.123, 0.5]
        example_id = "4"
        num = 0
        model_id = ModelData.model_01.ref('id')
        test_id = TestData.test_01.ref('id')
