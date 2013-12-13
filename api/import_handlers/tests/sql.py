# from bson import ObjectId
# from sqlparse.sql import Statement

# from utils import BaseTestCase


# class SqlMethodTests(BaseTestCase):
#     HANDLER_ID = '5170dd3a106a6c1631000000'
#     FIXTURES = ('models.json', 'datasets.json', 'importhandlers.json', )

#     def setUp(self):
#         super(SqlMethodTests, self).setUp()
#         self.Model = self.db.ImportHandler
#         self.obj = self.Model.find_one({'_id': ObjectId(self.HANDLER_ID)})

#     def test_build_query(self):
#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM some_table LIMIT 100;', limit=2),
#             'SELECT * FROM some_table LIMIT 2;'
#         )

#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM some_table LIMIT(100);', limit=3),
#             'SELECT * FROM some_table LIMIT 3;'
#         )

#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM some_table limit(100)', limit=3),
#             'SELECT * FROM some_table LIMIT 3'
#         )

#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM some_table;', limit=2),
#             'SELECT * FROM some_table LIMIT 2'
#         )

#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM some_table LIMIT ALL OFFSET 10', limit=4),
#             'SELECT * FROM some_table LIMIT 4 OFFSET 10'
#         )

#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM (SELECT name from some_table LIMIT 100) some_alias LIMIT 20;', limit=1),
#             'SELECT * FROM (SELECT name from some_table LIMIT 100) some_alias LIMIT 1;'
#         )

#         self.assertEquals(
#             self.obj.build_query('select * from (select name from some_table limit 100) some_alias', limit=2),
#             'select * from (select name from some_table limit 100) some_alias LIMIT 2'
#         )

#         self.assertEquals(
#             self.obj.build_query('SELECT * FROM some_table LIMIT 100; DELETE FROM some_table;', limit=2),
#             'SELECT * FROM some_table LIMIT 2; '
#         )

#     def test_check_sql(self):
#         with self.assertRaises(Exception):
#             self.obj.check_sql(
#                 'INSERT INTO some_table (id, name) VALUES (1, "Smth")')

#         with self.assertRaises(Exception):
#             self.obj.check_sql(
#                 'insert into some_table (id, name) value'
#                 ' (select id, name from other)')

#         with self.assertRaises(Exception):
#             self.obj.check_sql('UPDATE some_table SET name="new name"')

#         with self.assertRaises(Exception):
#             self.obj.check_sql(
#                 'DELETE FROM some_table; SELECT * FROM some_table;')

#         with self.assertRaises(Exception):
#             self.obj.check_sql('not sql')

#         self.assertIsInstance(self.obj.check_sql(
#             'SELECT * FROM some_table'), Statement)

#         self.assertIsInstance(self.obj.check_sql(
#             ' select * from some_table'), Statement)

#         st = self.obj.check_sql(
#             'SELECT * FROM some_table;DELETE FROM some_table;')
#         self.assertIsInstance(st, Statement)
#         self.assertEquals(st.get_type(), 'SELECT')
