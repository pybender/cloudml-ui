import os

DIR = os.path.dirname(__file__)

PIG_TEMPLATE = os.path.join(DIR, 'pig_template.txt').read()

XML_FIELD_TEMPLATE = '<field name="%(column_name)s" type="%(data_type)s" />'

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
