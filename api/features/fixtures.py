from fixture import DataSet


class FeatureSetData(DataSet):
    class bestmatch:
        schema_name = 'bestmatch'


class FeatureData(DataSet):
    class smth:
        name = 'smth'
        type = 'int'
        #features_set = FeatureSetData.bestmatch
        feature_set_id = FeatureSetData.bestmatch.ref('id')

    class hire_outcome_feature:
        input_format = 'dict'
        name = "hire_outcome"
        is_target_variable = True
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "text"
        feature_set_id = FeatureSetData.bestmatch.ref('id')

    class title_feature:
        input_format = 'dict'
        name = "title"
        is_target_variable = False
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "text"
        feature_set_id = FeatureSetData.bestmatch.ref('id')

    class name_feature:
        input_format = 'dict'
        name = "name"
        is_target_variable = False
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "text"
        feature_set_id = FeatureSetData.bestmatch.ref('id')

    class complex_feature:
        scaler = {
            "name": "feature scaler #3",
            "type": "MinMaxScaler",
            "copy": True
        }
        input_format = "dict"
        name = "transformed feature"
        transformer = {
            "name": "Test count #2 not is_predefined",
            "type": "Count",
            "charset": "aaa1"}
        is_target_variable = False
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "map"
        feature_set_id = FeatureSetData.bestmatch.ref('id')


class PredefinedTransformerData(DataSet):
    class transformer_01:
        name = u"my transformer"
        type = u"Dictionary"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {}

    class transformer_02:
        name = u"other transformer"
        type = u"Count"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {}


class PredefinedScalerData(DataSet):
    class scaler_01:
        name = u"my scaler"
        type = u"StandardScaler"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {"with_std": True}


class PredefinedClassifierData(DataSet):
    class lr_classifier:
        name = "name"
        type = "logistic regression"
        params = {"penalty": "l2"}
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"



class NamedFeatureTypeData(DataSet):
    class scaler_01:
        name = u"str_to_timezone"
        type = u"composite"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {"chain": [{"params": {"pattern": "UTC([-\\+]+\\d\\d).*"},
                             "type": "regex"},
                            {"type": "int"}]}
        input_format = None
