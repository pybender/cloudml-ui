import re
import json


def convert_name(name, to_text=False):
    """
    FeatureSet -> features_set
    FeatureSet -> Feature Set (if to_text)
    """
    if to_text:
        return re.sub("([a-z])([A-Z])", "\g<1> \g<2>", name)

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


ABERRANT_PLURAL_MAP = {
    'appendix': 'appendices',
    'barracks': 'barracks',
    'cactus': 'cacti',
    'child': 'children',
    'criterion': 'criteria',
    'deer': 'deer',
    'echo': 'echoes',
    'elf': 'elves',
    'embargo': 'embargoes',
    'focus': 'foci',
    'fungus': 'fungi',
    'goose': 'geese',
    'hero': 'heroes',
    'hoof': 'hooves',
    'index': 'indices',
    'knife': 'knives',
    'leaf': 'leaves',
    'life': 'lives',
    'man': 'men',
    'mouse': 'mice',
    'nucleus': 'nuclei',
    'person': 'people',
    'phenomenon': 'phenomena',
    'potato': 'potatoes',
    'self': 'selves',
    'syllabus': 'syllabi',
    'tomato': 'tomatoes',
    'torpedo': 'torpedoes',
    'veto': 'vetoes',
    'woman': 'women',
}

VOWELS = set('aeiou')


def pluralize(singular):
    """Return plural form of given lowercase singular word
    (English only). Based on
    ActiveState recipe http://code.activestate.com/recipes/413172/

    >>> pluralize('')
    ''
    >>> pluralize('goose')
    'geese'
    >>> pluralize('dolly')
    'dollies'
    >>> pluralize('genius')
    'genii'
    >>> pluralize('jones')
    'joneses'
    >>> pluralize('pass')
    'passes'
    >>> pluralize('zero')
    'zeros'
    >>> pluralize('casino')
    'casinos'
    >>> pluralize('hero')
    'heroes'
    >>> pluralize('church')
    'churches'
    >>> pluralize('x')
    'xs'
    >>> pluralize('car')
    'cars'

    """
    if not singular:
        return ''
    plural = ABERRANT_PLURAL_MAP.get(singular)
    if plural:
        return plural
    root = singular
    try:
        if singular[-1] == 'y' and singular[-2] not in VOWELS:
            root = singular[:-1]
            suffix = 'ies'
        elif singular[-1] == 's':
            if singular[-2] in VOWELS:
                if singular[-3:] == 'ius':
                    root = singular[:-2]
                    suffix = 'i'
                else:
                    root = singular[:-1]
                    suffix = 'ses'
            else:
                suffix = 'es'
        elif singular[-2:] in ('ch', 'sh'):
            suffix = 'es'
        else:
            suffix = 's'
    except IndexError:
        suffix = 's'
    plural = root + suffix
    return plural


# TODO: nsoliman 20140704 should we move these functions to the frontend instead?
def json_list_to_table(json_list):
    """
    Converts a list of json string to table structure, see :func: _dict_list_to_table
    :param json_list:
    :return:
    """
    return dict_list_to_table([json.loads(item) for item in json_list])


def dict_list_to_table(dict_list):
    """
    converts dict_list to a table structure, table structure is simply
    a dictionary with two keys, columns: these are the collective keys
    of all dictionary items. rows: these are the dictionary items themselves.
    This structure  is helpful client side to build html table out of list of
    json string
    :param dict_list:
    :return: {'columns':['c1', 'c2', ...], 'rows':[{}, {}, ...]}
    """
    columns = set()
    for item in dict_list:
        columns.update(item.keys())
    return {'columns': list(columns), 'rows': dict_list}