import unittest
import json

from api.base.utils import dict_list_to_table, json_list_to_table


class UtilsTestCase(unittest.TestCase):

    def test_dict_list_to_table(self):
        table = dict_list_to_table([{'C1': '11', 'C2': '12', 'C4': '13'},
                                    {'C1': '21', 'C2': '22', 'C3': '23'}])
        self.assertEqual(set(table['columns']), set(['C1', 'C2', 'C3', 'C4']))
        self.assertEqual(table['rows'], [{'C1': '11', 'C2': '12', 'C4': '13'},
                                         {'C1': '21', 'C2': '22', 'C3': '23'}])

    def test_json_list_to_table(self):
        table = json_list_to_table([json.dumps({'C1': '11', 'C2': '12', 'C4': '13'}),
                                    json.dumps({'C1': '21', 'C2': '22', 'C3': '23'})])
        self.assertEqual(set(table['columns']), set(['C1', 'C2', 'C3', 'C4']))
        self.assertEqual(table['rows'], [{'C1': '11', 'C2': '12', 'C4': '13'},
                                         {'C1': '21', 'C2': '22', 'C3': '23'}])