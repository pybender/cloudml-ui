from fixture import DataSet
from api.features.fixtures import FeatureSetData
from api.import_handlers.fixtures import ImportHandlerData


class ModelData(DataSet):
    class model_01:
        features_set_id = FeatureSetData.bestmatch.ref('id')
        test_import_handler_id = ImportHandlerData.import_handler_01.ref('id')
        train_import_handler_id = ImportHandlerData.import_handler_01.ref('id')
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "TrainedModel"
        comparable = True
        labels = ["0", "1"]
        import_params = ["start", "end"]
        error = ""
        feature_count = 37
        example_id = "opening_id"
        example_label = "opening_title"
        target_variable = "hire_outcome"
        weights_synchronized = False
        classifier = {
            "name": "Test Classifier",
            "params": {"penalty": "l2"},
            "type": "logistic regression"
        }

    class model_02:
        status = "Trained"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "OtherModel"
        comparable = True
        labels = ["0", "1"]

    class model_03:
        status = "New"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "NewModel"
        comparable = False
        labels = ["0", "1"]


class WeightData(DataSet):
    class weight_01:
        name = "opening_id"
        model_name = "TrainedModel"
        model_id = ModelData.model_01.ref('id')
        short_name = "opening_id"
        value = 0.4444
        is_positive = True
        css_class = "green"
        parent = None

    class weight_02:
        name = "contractor->dev_blurb->Over"
        model_name = "TrainedModel"
        model_id = ModelData.model_01.ref('id')
        short_name = "Over"
        value = 0.022345208915455828
        is_positive = True
        css_class = "green dark"
        parent = "contractor.dev_blurb"

    class weight_03:
        name = "opening"
        model_name = "TrainedModel"
        model_id = ModelData.model_01.ref('id')
        short_name = "opening"
