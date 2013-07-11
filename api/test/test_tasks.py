from bson import ObjectId

from utils import BaseTestCase


class TestTasksTests(BaseTestCase):
    """
    Tests of the celery tasks.
    """
    TEST_NAME = 'Test-1'
    FIXTURES = ('models.json', 'tests.json', 'examples.json')

    def setUp(self):
        super(TestTasksTests, self).setUp()
        self.test = self.db.Test.find_one({'name': self.TEST_NAME})

    def _set_probabilities(self, probabilities):
        for example in self.db.TestExample.find({'test_name': self.TEST_NAME}):
            label, prob = probabilities[example['id']]
            example['test_id'] = str(self.test._id)
            example['label'] = label
            example['prob'] = prob
            example.save()

    def test_calculate_confusion_matrix(self):
        from api.tasks import calculate_confusion_matrix

        self._set_probabilities({
            '1':  ('0', [0.3, 0.7]),
            '1a': ('0', [0.9, 0.1]),
            '2':  ('1', [0.3, 0.7]),
            '4':  ('1', [0.2, 0.8]),
        })

        self.assertEquals(calculate_confusion_matrix(self.test._id, 0), [[2, 2], [2, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.1), [[2, 2], [2, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.3), [[2, 1], [1, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.5), [[1, 1], [0, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.7), [[1, 1], [0, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 1), [[0, 0], [0, 0]])

        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 'wrong')
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, -1)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 1.2)
        self.assertRaises(ValueError, calculate_confusion_matrix, ObjectId(), 0.3)

        self._set_probabilities({
            '1':  ('0', [0.9, 0.1]),
            '1a': ('0', [0.9, 0.1]),
            '2':  ('1', [0.1, 0.9]),
            '4':  ('1', [0.1, 0.9]),
        })

        self.assertEquals(calculate_confusion_matrix(self.test._id, 0), [[2, 2], [2, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.1), [[2, 2], [2, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.3), [[2, 0], [0, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.5), [[2, 0], [0, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 0.7), [[2, 0], [0, 2]])
        self.assertEquals(calculate_confusion_matrix(self.test._id, 1), [[0, 0], [0, 0]])
