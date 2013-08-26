import sys
from mock import patch, MagicMock

from api.migrations import DbMigration
from utils import BaseTestCase


class MigrationCalls(object):
    _calls = []


class MigrationsTests(BaseTestCase):
    """
    Tests of DbMigration class.
    """

    @patch('api.migrations.DbMigration.get_migrations_module')
    def test_do_all_migrations(self, mock_get_module):
        mock_get_module.return_value = sys.modules[__name__]

        DbMigration.do_all_migrations()

        self.assertEquals(MigrationCalls._calls, [
            'Migration 1-1 was called',
            'Migration 2-1 was called',
            'Migration 2-2 was called',
        ])

        MigrationCalls._calls = []

        DbMigration.do_all_migrations(class_or_collection='others')

        self.assertEquals(MigrationCalls._calls, [
            'Migration 2-1 was called',
            'Migration 2-2 was called',
        ])

        MigrationCalls._calls = []

        DbMigration.do_all_migrations(class_or_collection='MockOtherModel')

        self.assertEquals(MigrationCalls._calls, [
            'Migration 2-1 was called',
            'Migration 2-2 was called',
        ])

        MigrationCalls._calls = []

        DbMigration.do_all_migrations(class_or_collection='fakes')

        self.assertEquals(MigrationCalls._calls, [
            'Migration 1-1 was called',
        ])


class MockModel(MagicMock):
    __collection__ = 'fakes'


class MockOtherModel(MagicMock):
    __collection__ = 'others'


class MockMigration1(DbMigration):
    DOC_CLASS = MockModel

    def allmigration01__fake(self):
        MigrationCalls._calls.append('Migration 1-1 was called')


class MockMigration2(DbMigration):
    DOC_CLASS = MockOtherModel

    def allmigration01__fake(self):
        MigrationCalls._calls.append('Migration 2-1 was called')

    def allmigration02__fake(self):
        MigrationCalls._calls.append('Migration 2-2 was called')
