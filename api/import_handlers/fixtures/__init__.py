# Authors: Nikolay Melnik <nmelnik@upwork.com>

import json
import os
import uuid

from fixture import DataSet
from api.accounts.fixtures import UserData
from ..models import XmlImportHandler as ImportHandler

DIR = os.path.dirname(__file__)
EXTRACT_XML = open(os.path.join(DIR, 'importhandler.xml'), 'r').read()
IMPORTHANDLER = open(os.path.join(DIR, 'importhandler.xml'), 'r').read()
IMPORTHANDLER_FROM_FIXTURES = open(os.path.join(
    DIR, 'importhandler_from_fixtures.xml'), 'r').read()
EXTRACT_TRAIN_XML = open(os.path.join(DIR, 'extract-train.xml'), 'r').read()
EXTRACT_OBSOLETE = open(os.path.join(DIR, 'obsolete_extract.xml'), 'r').read()


def get_importhandler(filename='extract-train.xml'):
    """
    Creates the import handler from fixtures file.
    """
    from ..models import fill_import_handler
    name = str(uuid.uuid1())
    handler = ImportHandler(name=name, import_params=['start', 'end'])
    data = open(os.path.join(DIR, filename), 'r').read()
    fill_import_handler(handler, data)
    handler.save()
    return handler


class PredefinedDataSourceData(DataSet):
    class datasource_01:
        name = "DataSource #1"
        type = "sql"
        db = {'conn': 'conn str', 'vendor': 'postgres'}
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"


class XmlImportHandlerData(DataSet):
    class import_handler_01:
        name = "Xml Handler 1"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        import_params = ['start', 'end']
        created_by = UserData.user_01

    class import_handler_02:
        name = "Xml Handler 2"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        import_params = ['start_date', 'end_date']
        created_by = UserData.user_02


class XmlDataSourceData(DataSet):
    class datasource_01:
        name = "ds"
        import_handler = XmlImportHandlerData.import_handler_01
        type = "db"
        params = dict(host="localhost", dbname="odw", vendor="postgres",
                      user="postgres", password="postgres")


class XmlQueryData(DataSet):
    class query_01:
        text = """SELECT qi.*,
        'class' || (trunc(random() * 2) + 1)::char hire_outcome
        FROM public.ja_quick_info qi
        where qi.file_provenance_date >= '#{start}'
        AND qi.file_provenance_date < '#{end}' LIMIT(100);"""


class XmlEntityData(DataSet):
    class xml_entity_01:
        name = "application"
        datasource = XmlDataSourceData.datasource_01
        import_handler = XmlImportHandlerData.import_handler_01
        query_obj = XmlQueryData.query_01
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"


class XmlFieldData(DataSet):
    class xml_field_01:
        name = "opening_id"
        type = "integer"
        entity = XmlEntityData.xml_entity_01

    class xml_field_02:
        name = "hire_outcome"
        type = "string"
        entity = XmlEntityData.xml_entity_01


class XmlInputParameterData(DataSet):
    class xml_parameter_01:
        name = "start"
        type = 'date'
        import_handler = XmlImportHandlerData.import_handler_01
        datasource = XmlDataSourceData.datasource_01

    class xml_parameter_02:
        name = "end"
        type = 'date'
        import_handler = XmlImportHandlerData.import_handler_01
        datasource = XmlDataSourceData.datasource_01


class DataSetData(DataSet):
    class dataset_01:
        name = "DS"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "8a7d1ae26efc11e395b420107a86d035.json"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/fixtures/ds.gz"
        filesize = 100
        records_count = 100
        time = 200
        data_fields = ["employer.country", "opening_id"]
        format = "json"
        uid = '8a7d1ae26efc11e395b420107a86d035'
        import_handler_id = 1
        import_handler_type = 'xml'

    class dataset_02:
        name = "DS 2"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "8a7d1ae26efc11e395b420107a86d036.json"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/fixtures/ds2.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "json"
        uid = '8a7d1ae26efc11e395b420107a86d036'
        import_handler_id = 1
        import_handler_type = 'xml'

    class dataset_03:
        name = "DS 3 (csv)"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "8a7d1ae26efc11e395b420107a86d037.csv"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/fixtures/ds_csv.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "csv"
        uid = '8a7d1ae26efc11e395b420107a86d037'
        import_handler_id = 1
        import_handler_type = 'xml'

    class dataset_04:
        name = "DS (pig)"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "8a7d1ae26efc11e395b420107a86d036.json"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/fixtures/ds2.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "json"
        uid = '8a7d1ae26efc11e395b420107a86d036'
        import_handler_id = 1
        import_handler_type = 'xml'
        pig_step = 1
        pig_row = {'opening': 1, 'title': 'Title', 'metric': 0.5}


IMPORT_HANDLER_FIXTURES = [
    XmlImportHandlerData,
    XmlEntityData,
    XmlFieldData,
    XmlDataSourceData,
    XmlInputParameterData,
    XmlQueryData
]
