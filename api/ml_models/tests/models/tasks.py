"""
Unittests for Model specific celery tasks
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import urllib
import tempfile
import numpy
from mock import patch

from api.base.test_utils import BaseDbTestCase
from api.ml_models.models import Model, Segment, Weight
from api.ml_models.fixtures import ModelData, TagData, DECISION_TREE, \
    DECISION_TREE_WITH_SEGMENTS, TREE_VISUALIZATION_DATA, MULTICLASS_MODEL, \
    MODEL_TRAINER, SEGMENTATION_MODEL
from api.import_handlers.models import DataSet
from api.import_handlers.fixtures import DataSetData


class ModelTasksTests(BaseDbTestCase):
    """
    Tests for the celery tasks
    """
    datasets = [DataSetData, ModelData]

    def setUp(self):
        super(ModelTasksTests, self).setUp()
        self.obj = Model.query.filter_by(
            name=ModelData.model_01.name).first()

    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    @patch('api.ml_models.models.Model.get_features_json')
    def test_train_model_task(self, mock_get_features_json, load_mock):
        from api.ml_models.tasks import train_model
        ds = DataSet.query.filter_by(
            name=DataSetData.dataset_03.name).first()
        load_mock.return_value = MODEL_TRAINER

        with open('./conf/features.json', 'r') as f:
            mock_get_features_json.return_value = f.read()
        res = train_model.run(
            dataset_ids=[ds.id], model_id=self.obj.id, user_id=1)
        self.assertTrue('Model trained' in res)
        self.assertEqual(self.obj.status, Model.STATUS_TRAINED, self.obj.error)
        self.assertTrue(ds.locked)

    @patch('api.amazon_utils.AmazonS3Helper.load_key')
    @patch('api.ml_models.models.Model.get_features_json')
    def test_model_segmentation(self, mock_get_features_json, load_mock):
        from api.ml_models.tasks import train_model
        ds = DataSet.query.filter_by(
            name=DataSetData.dataset_03.name).first()
        load_mock.return_value = SEGMENTATION_MODEL
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
            ValueError, generate_visualization_tree, invalid_model_id, 10)

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

    @patch('api.amazon_utils.AmazonS3Helper.get_download_url')
    @patch('api.amazon_utils.AmazonS3Helper.save_key')
    @patch('api.ml_models.models.Model.get_trainer')
    def test_transform_dataset_for_download_task(self, get_trainer_mock,
                                                 save_mock, dl_mock):
        model = Model.query.filter_by(name=ModelData.model_01.name).first()
        dataset = DataSet.query.first()

        from cloudml.trainer.store import TrainerStorage
        from api.ml_models.tasks import transform_dataset_for_download
        trainer = TrainerStorage.loads(MULTICLASS_MODEL)
        get_trainer_mock.return_value = trainer

        # check that nothing fails
        transform_dataset_for_download(model.id, dataset.id)

        direct_transform = model.transform_dataset(dataset)
        # repeat logic from task here except posting to Amazon S3
        temp_file = tempfile.NamedTemporaryFile()
        numpy.savez_compressed(temp_file, **direct_transform)
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

    @patch('api.amazon_utils.AmazonS3Helper.get_download_url')
    @patch('api.amazon_utils.AmazonS3Helper.save_key')
    @patch('api.ml_models.models.Model.get_trainer')
    def test_upload_segment_features_transformers_task(self, get_trainer_mock,
                                                       save_mock, dl_mock):
        from cloudml.trainer.store import TrainerStorage
        from api.ml_models.tasks import upload_segment_features_transformers
        from zipfile import ZipFile, ZIP_DEFLATED
        import os

        model = Model.query.filter_by(name=ModelData.model_01.name).first()

        trainer = TrainerStorage.loads(MODEL_TRAINER)
        get_trainer_mock.return_value = trainer
        for segment_name in trainer.features:
            s = Segment()
            s.name = segment_name
            s.records = 111
            s.model_id = model.id
            s.save()

        segment = Segment.query.filter(
            Segment.name == s.name).one()

        # check that nothing fails
        upload_segment_features_transformers(model.id, segment.id, 'json')

        # repeat logic from task here except posting to Amazon S3
        try:
            fformat = 'json'

            def _save_content(content, feature_name, transformer_type):
                filename = "{0}-{1}-{2}-data.{3}".format(segment.name,
                                                         feature_name,
                                                         transformer_type,
                                                         fformat)
                if fformat == 'csv':
                    import csv
                    import StringIO
                    si = StringIO.StringIO()
                    if len(content):
                        fieldnames = content[0].keys()
                        writer = csv.DictWriter(si, fieldnames=fieldnames)
                        writer.writeheader()
                        for c in content:
                            writer.writerow(c)
                    response = si.getvalue()
                else:
                    import json
                    response = json.dumps(content, indent=2)
                with open(filename, 'w') as fh:
                    fh.write(response)
                    fh.close()
                return filename

            trainer = model.get_trainer()
            if segment.name not in trainer.features:
                raise Exception("Segment %s doesn't exists in trained model" %
                                segment.name)
            files = []
            for name, feature in trainer.features[segment.name].iteritems():
                if "transformer" in feature and \
                                feature["transformer"] is not None:
                    try:
                        data = feature["transformer"].load_vocabulary()
                        files.append(_save_content(data, name,
                                                   feature["transformer-type"])
                                     )
                    except AttributeError:
                        continue

            arc_name = "{0}-{1}-{2}.zip".format(model.name, segment.name,
                                                fformat)
            with ZipFile(arc_name, "w") as z:
                for f in files:
                    z.write(f, compress_type=ZIP_DEFLATED)
                z.close()
            for f in files:
                os.remove(f)

            self.assertEqual(arc_name,
                             "{0}-default-json.zip".format(model.name))
            fh = open(arc_name, 'rb')
            z = ZipFile(fh)
            for name in z.namelist():
                outpath = "./"
                z.extract(name, outpath)
            file_list = z.namelist()
            fh.close()

            self.assertEqual(len(file_list), 2)
            self.assertEqual(
                set(file_list),
                set(["default-contractor.dev_blurb-Tfidf-data.json",
                     "default-contractor.dev_profile_title-Tfidf-data.json"]))
            fh = open("default-contractor.dev_blurb-Tfidf-data.json", 'r')
            content = fh.read()
            res = json.loads(content)
            self.assertEqual(set(res[0].keys()),
                             set(["word", "index", "weight"]))
        finally:
            for f in files:
                os.remove(f)
            if os.path.exists(arc_name):
                os.remove(arc_name)


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
