"""
Unittests for Model specific celery tasks
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import urllib
import tempfile
import numpy
from moto import mock_s3
from mock import patch

from api.base.test_utils import BaseDbTestCase
from api.ml_models.models import Model, Segment, Weight
from api.ml_models.fixtures import ModelData, TagData, DECISION_TREE, \
    DECISION_TREE_WITH_SEGMENTS, TREE_VISUALIZATION_DATA, MULTICLASS_MODEL
from api.import_handlers.models import DataSet
from api.import_handlers.fixtures import DataSetData
from api.base.resources.exceptions import NotFound


class ModelTasksTests(BaseDbTestCase):
    """
    Tests for the celery tasks
    """
    datasets = [DataSetData, ModelData]

    def setUp(self):
        super(ModelTasksTests, self).setUp()
        self.obj = Model.query.filter_by(
            name=ModelData.model_01.name).first()

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_task(self, mock_get_features_json, *mocks):
        from api.ml_models.tasks import train_model
        ds = DataSet.query.filter_by(
            name=DataSetData.dataset_03.name).first()

        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()
        res = train_model.run(
            dataset_ids=[ds.id], model_id=self.obj.id, user_id=1)
        self.assertTrue('Model trained' in res)
        self.assertEqual(self.obj.status, Model.STATUS_TRAINED, self.obj.error)
        self.assertTrue(ds.locked)

    @mock_s3
    @patch('api.ml_models.models.Model.get_features_json')
    def test_model_segmentation(self, mock_get_features_json, *mocks):
        from api.ml_models.tasks import train_model
        ds = DataSet.query.filter_by(
            name=DataSetData.dataset_03.name).first()

        with open('./conf/features_with_segmentation.json', 'r') as f:
            mock_get_features_json.return_value = f.read()
        res = train_model.run(
            dataset_ids=[ds.id], model_id=self.obj.id, user_id=1)
        self.assertTrue('Model trained' in res)
        self.assertEqual(self.obj.status, Model.STATUS_TRAINED, self.obj.error)
        self.assertTrue(self.obj.weights_synchronized)
        segments = Segment.query.filter_by(model=self.obj)
        self.assertEquals(segments.count(), 2)
        self.assertEqual(
            Weight.query.count(), 357)
        self.assertTrue(
            Weight.query.filter_by(segment=segments[0]).count())
        self.assertTrue(
            Weight.query.filter_by(segment=segments[1]).count())

    @patch('api.ml_models.models.Model.get_trainer')
    def test_generate_visualization_tree(self, get_trainer_mock):
        """
        Checks generate_visualization_tree task with decision tree
        clf without segmentation.
        """
        # Using non existance model
        from api.ml_models.tasks import generate_visualization_tree, \
            VisualizationException
        invalid_model_id = -101
        self.assertRaises(
            NotFound, generate_visualization_tree, invalid_model_id, 10)

        # Trying to generate tree for logistic regression classifier
        self.assertRaises(
            VisualizationException,
            generate_visualization_tree, self.obj.id, 10)

        # Re-generating tree for decision tree classifier
        model = Model.query.filter_by(name='decision_tree_clf_model').one()
        from cloudml.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(DECISION_TREE)
        get_trainer_mock.return_value = trainer
        # In this model 'all_weights' not saved to visualization_data
        # while training.
        # So it's inpossible to re-generate tree.
        self.assertRaises(
            VisualizationException, generate_visualization_tree,
            model.id, deep=2)

        from cloudml.trainer.trainer import DEFAULT_SEGMENT
        model.visualization_data = {DEFAULT_SEGMENT: TREE_VISUALIZATION_DATA}
        model.save()

        from random import randint
        deep = randint(2, 10)
        res = generate_visualization_tree(model.id, deep=deep)
        self.assertEquals(res, "Tree visualization was completed")
        print "using deep %s" % deep
        self.assertEquals(
            model.visualization_data[DEFAULT_SEGMENT]['parameters']['deep'],
            deep)
        tree = model.visualization_data[DEFAULT_SEGMENT]['tree']
        self.assertEquals(determine_deep(tree), deep)

    @patch('api.ml_models.models.Model.get_trainer')
    def test_generate_visualization_tree_with_segments(
            self, get_trainer_mock):
        """
        Checks generate_visualization_tree task with decision
        tree clf with segmentation.
        """
        from api.ml_models.tasks import generate_visualization_tree, \
            VisualizationException
        from cloudml.trainer.store import TrainerStorage
        trainer = TrainerStorage.loads(DECISION_TREE_WITH_SEGMENTS)
        get_trainer_mock.return_value = trainer

        segments = {2: 5, 3: 4, 5: 1, 4: 1}
        model = Model.query.filter_by(name='decision_tree_clf_model').one()
        model.create_segments(segments)
        model.group_by = 'contractor.dev_eng_skill'
        model.visualization_data = {}
        for seg in segments.keys():
            model.visualization_data[seg] = TREE_VISUALIZATION_DATA
        model.save()

        from random import randint
        deep = randint(2, 4)
        res = generate_visualization_tree(model.id, deep=deep)
        self.assertEquals(res, "Tree visualization was completed")
        print "using deep %s" % deep
        self.assertEquals(
            model.visualization_data['2']['parameters']['deep'], deep)
        tree = model.visualization_data['5']['tree']
        self.assertEquals(determine_deep(tree), deep)

    @patch('api.ml_models.models.Model.get_trainer')
    def test_transform_dataset_for_download_task(self, get_trainer_mock):
        model = Model.query.filter_by(name=ModelData.model_01.name).first()
        dataset = DataSet.query.first()

        from cloudml.trainer.store import TrainerStorage
        from api.ml_models.tasks import transform_dataset_for_download
        trainer = TrainerStorage.loads(MULTICLASS_MODEL)
        get_trainer_mock.return_value = trainer

        direct_transform = model.transform_dataset(dataset)

        url = transform_dataset_for_download(model.id, dataset.id)

        temp_file = tempfile.NamedTemporaryFile()
        urllib.urlretrieve(url, temp_file.name)
        temp_file.seek(0)

        s3_transform = numpy.load(temp_file)

        self.assertEqual(len(s3_transform.files), len(direct_transform))
        for segment in s3_transform:
            s3_segment = s3_transform[segment].tolist()
            direct_segment = direct_transform[segment]
            self.assertEqual(s3_segment['Y'], direct_segment['Y'])
            self.assertTrue((s3_segment['X'].toarray() ==
                             direct_segment['X'].toarray()).all())

        # TODO : Requires prerun or some how waiting for task to run
        # downloads = AsyncTask.get_current_by_object(
        #     model, 'api.ml_models.tasks.transform_dataset_for_download')
        # self.assertEqual(1, len(downloads))


def determine_deep(tree):
    def recurse(node, current_deep):
        if 'children' in node:
            current_deep += 1
            subnodes = node['children']
            if subnodes:
                left = recurse(subnodes[0], current_deep)
                right = recurse(subnodes[1], current_deep)
                return max(left, right)
        return current_deep
    return recurse(tree, 0)
