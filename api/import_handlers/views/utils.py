PIG_TEMPLATE = """register 's3://odesk-match-staging/pig/lib/elephant-bird-core-4.4.jar';
register 's3://odesk-match-staging/pig/lib/elephant-bird-pig-4.4.jar';
register 's3://odesk-match-staging/pig/lib/elephant-bird-hadoop-compat-4.4.jar';
register 's3://odesk-match-staging/pig/lib/piggybank-0.12.0.jar';

result = LOAD '$dataset*' USING org.apache.pig.piggybank.storage.CSVExcelStorage(',', 'YES_MULTILINE') AS (

{0}

);"""

SCHEMA_INFO_FIELDS = [
    'column_name', 'data_type', 'character_maximum_length',
    'is_nullable', 'column_default']

PIG_FIELDS_MAP = {
    'integer': 'integer',
    'smallint': 'integer',
    'bigint': 'long',
    'character varying': 'chararray',
    'text': 'chararray',
    'double': 'double',
    'float': 'float',
    'decimal': 'double',
    'numeric': 'double',
    'boolean': 'boolean',
    'ARRAY': 'tuple',
    'json': 'chararray'
}


def get_pig_type(field):
    type_ = field['data_type']
    if type_ in PIG_FIELDS_MAP:
        return PIG_FIELDS_MAP[type_]
    if type_.startswith('timestamp'):
        return 'chararray'
    if type_.startswith('double'):
        return 'double'
    return "unknown"


def construct_pig_sample(fields_data):
    fields_str = ""
    is_first = True
    for field in fields_data:
        if not is_first:
            fields_str += "\n, "
        fields_str += "{0}:{1}".format(field['column_name'],
                                       get_pig_type(field))
        is_first = False
    return fields_str


def isfloat(x):
    try:
        a = float(x)
    except ValueError, TypeError:
        return False
    else:
        return True


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError, TypeError:
        return False
    else:
        return a == b
