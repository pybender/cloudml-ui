import json
import os

from fixture import DataSet
from api.accounts.fixtures import UserData

DIR = os.path.dirname(__file__)
IMPORT_HANDLER_01 = os.path.join(DIR, 'import_handler_01.json')


class ImportHandlerData(DataSet):
    class import_handler_01:
        name = "Handler 1"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        import_params = ['start', 'end', 'category']
        data = json.loads(open(IMPORT_HANDLER_01, 'r').read())


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
        filename = "api/import_handlers/ds.gz"
        filesize = 100
        records_count = 100
        time = 200
        data_fields = ["employer.country", "opening_id"]
        format = "json"
        uid = '8a7d1ae26efc11e395b420107a86d035'
        import_handler_id = 1
        import_handler_type = 'json'

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
        filename = "api/import_handlers/ds2.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "json"
        uid = '8a7d1ae26efc11e395b420107a86d036'
        import_handler_id = 1
        import_handler_type = 'json'

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
        filename = "api/import_handlers/ds_csv.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "csv"
        uid = '8a7d1ae26efc11e395b420107a86d037'
        import_handler_id = 1
        import_handler_type = 'json'

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
        filename = "api/import_handlers/ds2.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "json"
        uid = '8a7d1ae26efc11e395b420107a86d036'
        import_handler_id = 1
        import_handler_type = 'xml'
        pig_step = 1
        pig_row = {'opening': 1, 'title': 'Title', 'metric': 0.5}


class PredefinedDataSourceData(DataSet):
    class datasource_01:
        name = "DataSource #1"
        type = "sql"
        db = {'conn': 'conn str', 'vendor': 'postgres'}
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"


class XmlImportHandlerData(DataSet):
    class xml_import_handler_01:
        name = "Xml Handler 1"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        import_params = ['start', 'end', 'category']
        created_by = UserData.user_01

    class xml_import_handler_02:
        name = "Xml Handler 2"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        import_params = ['start', 'end', 'category']
        created_by = UserData.user_02


class XmlDataSourceData(DataSet):
    class xml_datasource_01:
        name = "ds"
        import_handler = XmlImportHandlerData.xml_import_handler_01
        type = "db"
        params = dict(host="localhost", dbname="odw", vendor="postgres",
                      user="postgres", password="postgres")


class XmlEntityData(DataSet):
    class xml_entity_01:
        name = "something"
        import_handler = XmlImportHandlerData.xml_import_handler_01
        datasource = XmlDataSourceData.xml_datasource_01
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"


class XmlFieldData(DataSet):
    class xml_field_01:
        name = "opening_id"
        type = "integer"
        entity = XmlEntityData.xml_entity_01


class XmlInputParameterData(DataSet):
    class xml_parameter_01:
        name = "start_date"
        type = 'date'
        import_handler = XmlImportHandlerData.xml_import_handler_01
        datasource = XmlDataSourceData.xml_datasource_01

    class xml_parameter_02:
        name = "end_date"
        type = 'date'
        import_handler = XmlImportHandlerData.xml_import_handler_01
        datasource = XmlDataSourceData.xml_datasource_01
