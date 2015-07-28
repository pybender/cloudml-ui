# Authors: Nikolay Melnik <nmelnik@upwork.com>

import os
import json
from fixture import DataSet

DIR = os.path.dirname(__file__)
FEATURES_STR = open(os.path.join(DIR, 'features.json'), 'r').read()
FEATURES_JSON = json.loads(FEATURES_STR)
TRANSFORMER_STR = open(os.path.join(DIR, 'transformer.json'), 'r').read()
TRANSFORMER_JSON = json.loads(FEATURES_STR)


class FeatureSetData(DataSet):
    class bestmatch:
        schema_name = 'bestmatch'


class FeatureData(DataSet):
    class smth:
        name = 'feature-title'
        type = 'int'
        feature_set = FeatureSetData.bestmatch
        params = {}
        transformer = {}
        scaler = {}

    class hire_outcome_feature:
        input_format = 'dict'
        name = "hire_outcome"
        is_target_variable = True
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "text"
        feature_set = FeatureSetData.bestmatch

    class title_feature:
        input_format = 'dict'
        name = "title"
        is_target_variable = False
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "text"
        feature_set = FeatureSetData.bestmatch

    class name_feature:
        input_format = 'dict'
        name = "name"
        is_target_variable = False
        default = "smth"
        required = True
        params = {"mappings": {"class2": 0, "class1": 1}}
        type = "text"
        feature_set = FeatureSetData.bestmatch

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
        feature_set = FeatureSetData.bestmatch

    class disabled_feature:
        name = 'disabled_feature'
        type = 'int'
        feature_set = FeatureSetData.bestmatch
        disabled = True


class PredefinedScalerData(DataSet):
    class scaler_01:
        name = u"my scaler"
        type = u"StandardScaler"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {"with_std": True}

    class scaler_02:
        name = u"my scaler #2"
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

    class lr_classifier_01:
        name = "another classifier"
        type = "logistic regression"
        params = {"penalty": "l2", "C": "1"}
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"


class NamedFeatureTypeData(DataSet):
    class type_01:
        name = u"str_to_timezone"
        type = u"composite"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {"chain": [{"params": {"pattern": "UTC([-\\+]+\\d\\d).*"},
                             "type": "regex"},
                            {"type": "int"}]}
        input_format = None

    class type_02:
        name = u"str_to_timezone2"
        type = u"composite"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        params = {"chain": [{"params": {"pattern": "UTC([-\\+]+\\d\\d).*"},
                             "type": "regex"},
                            {"type": "int"}]}
        input_format = None
