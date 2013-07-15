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
        self.examples_count = self.db.TestExample.find({'test_name': self.TEST_NAME}).count()

    def _set_probabilities(self, probabilities):
        for example in self.db.TestExample.find({'test_name': self.TEST_NAME}):
            label, prob = probabilities[example['id']]
            example['test_id'] = str(self.test._id)
            example['label'] = label
            example['prob'] = prob
            example.save()

    def test_calculate_confusion_matrix(self):
        from api.tasks import calculate_confusion_matrix

        def _assertMatrix(w0, w1, expected):
            result = calculate_confusion_matrix(self.test._id, w0, w1)
            self.assertEquals(result, expected)
            self.assertEquals(self.examples_count, sum([sum(row) for row in result]))

        self._set_probabilities({
            '1':  ('0', [0.3, 0.7]),
            '1a': ('0', [0.9, 0.1]),
            '2':  ('1', [0.3, 0.7]),
            '4':  ('1', [0.2, 0.8]),
        })

        _assertMatrix(1, 1, [[1, 1], [0, 2]])
        _assertMatrix(0.5, 0.5, [[1, 1], [0, 2]])
        _assertMatrix(1, 10, [[0, 2], [0, 2]])
        _assertMatrix(1, 100, [[0, 2], [0, 2]])
        _assertMatrix(10, 1, [[2, 0], [2, 0]])
        _assertMatrix(100, 1, [[2, 0], [2, 0]])
        _assertMatrix(0, 1, [[0, 2], [0, 2]])
        _assertMatrix(1, 0, [[2, 0], [2, 0]])
        _assertMatrix(1, 3, [[1, 1], [0, 2]])
        _assertMatrix(3, 1, [[2, 0], [1, 1]])

        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 0, 0)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, -1, 1)
        self.assertRaises(ValueError, calculate_confusion_matrix, self.test._id, 1, -1)
        self.assertRaises(ValueError, calculate_confusion_matrix, ObjectId(), 1, 1)
