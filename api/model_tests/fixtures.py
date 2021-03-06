"""
DB fixtures for TestResult and TestExample models.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from fixture import DataSet

from api.ml_models.fixtures import ModelData
from api.import_handlers.fixtures import DataSetData


class TestResultData(DataSet):
    class test_01:
        name = "Test-1"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "TrainedModel"
        parameters = {}
        metrics = {}
        examples_count = 100
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        classes_set = []
        accuracy = 0.95
        model = ModelData.model_01
        dataset = DataSetData.dataset_01

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
        classes_set = []
        accuracy = 0.95
        model = ModelData.model_01
        dataset = DataSetData.dataset_01

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
        error = ""
        data = {}
        classes_set = []
        accuracy = 0.95
        model = ModelData.model_01
        dataset = DataSetData.dataset_01

    class test_04:
        name = "Test-4"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "TrainedModel"
        parameters = {}
        metrics = {}
        examples_count = 0
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        classes_set = []
        accuracy = 0
        model = ModelData.model_01
        dataset = DataSetData.dataset_01

    class test_05:
        name = "Test-5"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = ModelData.model_03.name
        parameters = {}
        metrics = {}
        examples_count = 0
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        classes_set = []
        accuracy = 0
        model = ModelData.model_03
        dataset = DataSetData.dataset_01

    class test_06:
        name = "Test-6"
        status = "Completed"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        model_name = "model_multiclass_correct_labels"
        parameters = {}
        metrics = {}
        examples_count = 100
        examples_fields = ["hire_outcome", "application_id"]
        error = ""
        classes_set = []
        accuracy = 0.95
        model = ModelData.model_multiclass_1
        dataset = DataSetData.dataset_01


class TestExampleData(DataSet):
    class test_example_01:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-1"
        pred_label = "0"
        label = "1"
        test_name = "Test-1"
        model_name = "TrainedModel"
        weighted_data_input = {}
        prob = [0.6, 0.4]
        example_id = "1"
        num = 0
        model = ModelData.model_01
        test_result = TestResultData.test_01
        data_input = {
            'opening_id': "201913099",
            'employer->country': 'USA',
            'contractor->dev_blurb': "Over ten years experience successfully "
                                     "performing a number of data entry"
                                     " and clerical tasks.",
            'contractor->dev_timezone': "",
            "employer->op_country_tz": "",
            "employer->op_timezone": "",
            'tsexams': {
                'Some Exam': 5.0
            }
        }
        vect_data = [0.123, 0.0] * 217

    class test_example_02:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-2"
        pred_label = "1"
        label = "1"
        test_name = "Test-1"
        model_name = "TrainedModel"
        weighted_data_input = {}
        prob = [0.1, 0.9]
        example_id = "1a"
        num = 1
        model = ModelData.model_01
        test_result = TestResultData.test_01
        data_input = {
            'opening_id': "201913099",
            'employer->country': 'Canada'
        }
        weighted_data_input = {
            'opening_id': "201913099",
            'employer->country': 'Canada'}

    class test_example_03:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-3"
        pred_label = "1"
        label = "0"
        test_name = "Test-1"
        model_name = "TrainedModel"
        weighted_data_input = {}
        prob = [0.05, 0.95]
        example_id = "2"
        num = 3
        model = ModelData.model_01
        test_result = TestResultData.test_01
        data_input = {
            'opening_id': "201913099",
            'employer->country': 'USA'
        }

    class test_example_04:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #2-3"
        pred_label = "1"
        label = "0"
        test_name = "Test-2"
        model_name = "TrainedModel"
        weighted_data_input = {}
        prob = [0.5, 0.5]
        example_id = "3"
        locked = True
        num = 0
        model = ModelData.model_01
        test_result = TestResultData.test_02
        data_input = {
            'opening_id': "201913099",
            'employer->country': 'USA'
        }

    class test_example_05:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some OtherModel Example #1-1"
        pred_label = "1"
        label = "0"
        test_name = "Test-1"
        model_name = "OtherModel"
        weighted_data_input = {}
        prob = [0.5, 0.5]
        example_id = "4"
        num = 0
        model = ModelData.model_01
        test_result = TestResultData.test_01
        data_input = {
            'opening_id': "201913099"
        }

    class test_example_06:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #1-1"
        pred_label = "1"
        label = "0"
        test_name = TestResultData.test_02.name
        model_name = ModelData.model_01.name
        weighted_data_input = {}
        prob = [0.123, 0.5]
        example_id = "4"
        num = 0
        model = ModelData.model_01
        test_result = TestResultData.test_02
        data_input = {
            'opening_id': "201913099",
            'employer->country': 'Ukraine'
        }

    class test_example_07:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #6-1"
        pred_label = "1"
        label = "0"
        test_name = "Test-6"
        model_name = "model_multiclass_correct_labels"
        weighted_data_input = {}
        prob = [0.6, 0.3, 0.1]
        example_id = "1"
        num = 1
        model = ModelData.model_multiclass_1
        test_result = TestResultData.test_06
        data_input = {
        }

    class test_example_08:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #6-2"
        pred_label = "1"
        label = "0"
        test_name = "Test-6"
        model_name = "model_multiclass_correct_labels"
        weighted_data_input = {}
        prob = [0.3, 0.5, 0.2]
        example_id = "1"
        num = 0
        model = ModelData.model_multiclass_1
        test_result = TestResultData.test_06
        data_input = {
        }

    class test_example_09:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #6-3"
        pred_label = "0"
        label = "1"
        test_name = "Test-6"
        model_name = "model_multiclass_correct_labels"
        weighted_data_input = {}
        prob = [0.6, 0.3, 0.1]
        example_id = "1"
        num = 1
        model = ModelData.model_multiclass_1
        test_result = TestResultData.test_06
        data_input = {
        }

    class test_example_10:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #6-4"
        pred_label = "0"
        label = "1"
        test_name = "Test-6"
        model_name = "model_multiclass_correct_labels"
        weighted_data_input = {}
        prob = [0.3, 0.5, 0.2]
        example_id = "1"
        num = 0
        model = ModelData.model_multiclass_1
        test_result = TestResultData.test_06
        data_input = {
        }

    class test_example_11:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #6-5"
        pred_label = "1"
        label = "2"
        test_name = "Test-6"
        model_name = "model_multiclass_correct_labels"
        weighted_data_input = {}
        prob = [0.6, 0.3, 0.1]
        example_id = "1"
        num = 1
        model = ModelData.model_multiclass_1
        test_result = TestResultData.test_06
        data_input = {
        }

    class test_example_12:
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Some Example #6-6"
        pred_label = "1"
        label = "2"
        test_name = "Test-6"
        model_name = "model_multiclass"
        weighted_data_input = {}
        prob = [0.3, 0.5, 0.2]
        example_id = "1"
        num = 0
        model = ModelData.model_multiclass_1
        test_result = TestResultData.test_06
        data_input = {
        }
