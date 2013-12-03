from fixture import DataSet
from api.features.fixtures import FeatureSetData


class ModelData(DataSet):
    class model_01:
        name = "Model 1"
        #features_set = FeatureSetData.bestmatch
        features_set_id = FeatureSetData.bestmatch.ref('id')
