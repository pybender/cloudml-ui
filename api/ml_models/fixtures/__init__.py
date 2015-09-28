"""
Database fixtures for Models.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import os
import json

from fixture import DataSet
from api.features.fixtures import FeatureSetData
from api.import_handlers.fixtures import XmlImportHandlerData as ImportHandlerData


DIR = os.path.dirname(__file__)
TREE_VISUALIZATION_DATA = json.loads(open(os.path.join(
    DIR, 'tree_visualization_data.json'), 'r').read())
INVALID_MODEL = open(os.path.join(
    DIR, 'invalid_model.dat'), 'r').read()
MULTICLASS_MODEL = open(os.path.join(
    DIR, 'multiclass-trainer.dat'), 'r').read()
MODEL_TRAINER = open(os.path.join(
    DIR, 'model.dat'), 'r').read()
DECISION_TREE_WITH_SEGMENTS = open(os.path.join(
    DIR, 'decision_tree_segments.dat'), 'r').read()
DECISION_TREE = open(os.path.join(
    DIR, 'decision_tree.dat'), 'r').read()
MODELS_COUNT = 7


class ModelData(DataSet):
    class model_01:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
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
        weights_synchronized = True
        status = "Trained"
        trainer = "trainer_file"
        classifier = {
            "name": "Test Classifier",
            "params": {"penalty": "l2"},
            "type": "logistic regression"
        }
        visualization_data = {}

    class model_02:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        status = "Trained"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "OtherModel"
        comparable = True

    class model_03:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        status = "New"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "NewModel"
        comparable = False

    class model_multiclass:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        status = "Trained"
        weights_synchronized = True
        trainer = "trainer_file"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "model_multiclass"
        comparable = True
        labels = ["1", "2", "3"]

    class model_multiclass_1:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        status = "Trained"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "model_multiclass_correct_labels"
        comparable = True
        labels = ["0", "1", "2"]

    class model_04:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        status = "New"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Model with Xml IH"
        comparable = False

    class model_05:
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        status = "New"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "Model with Xml IH Featuureless"
        comparable = False

    class decision_tree_clf:
        features_set = FeatureSetData.bestmatch
        test_import_handler = ImportHandlerData.import_handler_01
        train_import_handler = ImportHandlerData.import_handler_01
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        name = "decision_tree_clf_model"
        comparable = True
        labels = ["0", "1"]
        import_params = ["start", "end"]
        error = ""
        feature_count = 37
        example_id = "opening_id"
        example_label = "opening_title"
        target_variable = "hire_outcome"
        weights_synchronized = False
        status = "Trained"
        trainer = "trainer_file"
        classifier = {
            "type": "decision tree classifier",
            "params": {
                "splitter": "best",
                "n_jobs": "1",
                "penalty": "l2",
                "min_samples_leaf": 1,
                "n_estimators": "10",
                "min_samples_split": 2,
                "criterion": "gini",
                "max_features": "auto"
            }
        }


class SegmentData(DataSet):

    class segment_01:
        name = "default"
        records = 87
        model = ModelData.model_01

    class segment_02:
        name = "default"
        records = 87
        model = ModelData.model_02

    class segment_multiclass_01:
        name = "True"
        records = 87
        model = ModelData.model_multiclass

    class segment_multiclass_02:
        name = "False"
        records = 87
        model = ModelData.model_multiclass


class WeightData(DataSet):
    class weight_01:
        name = "opening_id"
        model_name = ModelData.model_01.name
        model = ModelData.model_01
        segment = SegmentData.segment_01
        short_name = "opening_id"
        value = 0.4444
        is_positive = True
        css_class = "green"
        parent = ''
        class_label = '1'

    class weight_02:
        name = "contractor->dev_blurb->Over"
        model_name = ModelData.model_01.name
        model = ModelData.model_01
        segment = SegmentData.segment_01
        short_name = "Over"
        value = 0.022345208915455828
        is_positive = True
        css_class = "green dark"
        parent = "contractor.dev_blurb"
        class_label = '1'

    class weight_03:
        name = "opening"
        model_name = ModelData.model_01.name
        model = ModelData.model_01
        segment = SegmentData.segment_01
        short_name = "opening"
        value = -0.022345208915455828
        is_positive = False
        css_class = "red dark"
        parent = ''
        class_label = '1'

    class weight_01_model02:
        name = "opening_id"
        model_name = ModelData.model_02.name
        model = ModelData.model_02
        segment = SegmentData.segment_02
        short_name = "opening_id"
        value = -0.4444
        is_positive = False
        css_class = "red dark"
        parent = ''

    class weight_02_model_02:
        name = "contractor->dev_blurb->Over"
        model_name = ModelData.model_02.name
        model = ModelData.model_02
        segment = SegmentData.segment_02
        short_name = "Over"
        value = -0.022345208915455828
        is_positive = False
        css_class = "red"
        parent = "contractor.dev_blurb"

    class weight_03_model_02:
        name = "opening"
        model_name = ModelData.model_02.name
        model = ModelData.model_02
        segment = SegmentData.segment_02
        short_name = "opening"
        value = 0.022345208915455828
        is_positive = True
        css_class = "green"
        parent = ''

    class weight_multiclass_01:
        name = "multiclass_opening_id"
        model_name = ModelData.model_multiclass.name
        model = ModelData.model_multiclass
        segment = SegmentData.segment_multiclass_01
        short_name = "opening_id"
        value = 0.4444
        is_positive = True
        css_class = "green"
        parent = ''
        class_label = "1"

    class weight_multiclass_02:
        name = "multiclass_contractor->dev_blurb->Over"
        model_name = ModelData.model_multiclass.name
        model = ModelData.model_multiclass
        segment = SegmentData.segment_multiclass_01
        short_name = "Over"
        value = -0.022345208915455828
        is_positive = False
        css_class = "green dark"
        parent = "contractor.dev_blurb"
        class_label = "2"

    class weight_multiclass_03:
        name = "multiclass_opening"
        model_name = ModelData.model_multiclass.name
        model = ModelData.model_multiclass
        segment = SegmentData.segment_multiclass_01
        short_name = "opening"
        value = -0.022345208915455828
        is_positive = False
        css_class = "red dark"
        parent = ''
        class_label = "3"

    class weight_multiclass_04:
        name = "multiclass_opening2"
        model_name = ModelData.model_multiclass.name
        model = ModelData.model_multiclass
        segment = SegmentData.segment_multiclass_01
        short_name = "opening2"
        value = 0.022345208915455828
        is_positive = True
        css_class = "red dark"
        parent = ''
        class_label = "3"


class WeightsCategoryData(DataSet):
    class weightcategory_01:
        name = "contractor"
        model_name = ModelData.model_01.name
        model = ModelData.model_01
        short_name = "contractor"
        parent = ""


class TagData(DataSet):
    class tag_01:
        text = "tag"
        count = 2

    class tag_02:
        text = "tag2"
        count = 3


class TransformerData(DataSet):
    class transformer_01:
        name = "bestmatch"
        status = "New"
        field_name = "contractor.dev_blurb"
        feature_type = "text"
        type = "Tfidf"
        params = {
            "ngram_range_min": 1,
            "ngram_range_max": 1,
            "min_df": 5
        }
        train_import_handler = ImportHandlerData.import_handler_01
