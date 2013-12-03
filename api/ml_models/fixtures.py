from fixture import DataSet
from api.features.fixtures import FeatureSetData


class ModelData(DataSet):
    class model_01:
        features_set_id = FeatureSetData.bestmatch.ref('id')
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
