import math
import sys
import logging
import re
from api import app


TONES = ['lightest', 'lighter', 'light', 'dark', 'darker', 'darkest']


def calc_weights_css(weights, css_cls):
    """
    Determines tones of color dependly of weight value.
    """
    def cmp_func(a):
        return abs(a['weight'])

    def get_min_none_zero(weights):
        none_zero_weights = [w for w in weights if w['weight'] != 0]
        if len(none_zero_weights) > 0:
            return min(none_zero_weights, key=cmp_func)['weight']
        else:
            return 0.0

    def normalize_weights(weights, min_weight):
        weights = [{'name': item['name'],
                    'weight': item['weight'],
                    'feature_weight': item['feature_weight'],
                    'transformed_weight': math.log(
                        abs(item['weight'] / min_weight))
                    if item['weight'] != 0 else 0}
                   for item in weights]
        weights.sort(key=cmp_func)
        if min_weight > 0:
            weights.reverse()
        return weights

    min_none_zero_weight = get_min_none_zero(weights)
    weights = normalize_weights(weights, min_none_zero_weight)
    tones = ['lightest', 'lighter', 'light', 'dark', 'darker', 'darkest']
    tones_count = len(tones)

    def cmp_func(a):
        return abs(a['transformed_weight'])
    wmax = max(weights, key=cmp_func)['transformed_weight']
    delta = round(wmax / tones_count)
    for i in xrange(tones_count):
        tone = tones[i]
        css_class = "%s %s" % (css_cls, tone)
        limit = i * delta
        for item in weights:
            if abs(item['transformed_weight']) >= limit:
                item['css_class'] = css_class
    return weights


# TODO: unused code
def weights2tree(weights):  # pragma: no cover
    """
    Converts weights list to tree dict.
    """
    tree = {}
    for item in weights:
        name = item['name']
        splitted = name.split(".")
        count = len(splitted)
        parent_node = tree
        for i, part in enumerate(splitted):
            if i == (count - 1):
                param = {'full_name': name,
                         'name': part,
                         'value': item['weight'],
                         'css_class': item['css_class']}
                parent_node[part] = param

            if part not in parent_node:
                parent_node[part] = {}

            parent_node = parent_node[part]
    return tree


def get_example_params(model_weights, row, vect_row):
    """ Adds weights and color tones to each test example parameter.
    Note: Uses real data when calculating this values:
        weight = model parameter weight * parameter value.

    :param model_weights:
    :param row: parameters values dict
    :param vect_row: vectorized parameters values (dict)
    """
    if not row:
        return {}

    result = {}
    weights_dict = dict([(weight.name, weight.__dict__)
                         for weight in model_weights])

    def try_set_item(result, name, value, subkey=None,
                     value_type=None):
        """
        Tries to find model parameters weight for:
            * name
            * name->value
            * name->value in lowercase
            * name=value
        and set weight for test example parameter.
        """
        def _get_item(key, value):
            wdict = weights_dict[key]
            vect_val = vect_row[key]
            return {'weight': wdict['value'] * vect_val,
                    'model_weight': wdict['value'],
                    'value': value,
                    'css_class': 'fill me',
                    'vect_value': vect_val}

        def _check(key):
            if key in weights_dict:
                item = _get_item(key, value)
                if subkey:
                    result[name]['type'] = value_type
                    if 'weights' not in result[name]:
                        result[name]['weights'] = {}
                    result[name]['weights'][subkey] = item
                else:
                    result[name] = item
                return True

        key = "%s->%s" % (name, subkey) if subkey else name
        if _check(key):
            return True
        elif isinstance(value, basestring):
            if _check("%s->%s" % (name, value)):
                return True
            elif _check("%s->%s" % (name, value.lower())):
                return True
            else:
                key = "%s=%s" % (name, value)
                return _check(key)
        return False

    for key, value in row.iteritems():
        result[key] = {'value': value}
        if not try_set_item(result, key, value):
            if isinstance(value, basestring):
                # try to find each word from the value
                rgx = re.compile("(\w[\w']*)")
                words = rgx.findall(value)
                for word in words:
                    word = word.lower().strip()
                    try_set_item(result, key, value, word, 'list')
            elif isinstance(value, dict):
                for dkey, dvalue in value.iteritems():
                    try_set_item(result, key, dvalue, dkey, 'dict')
    _tone_weights(result.values())
    return result


def _tone_weights(weights, value_name='weight'):
    """
    Tones test example parameters weights tree with css styles:
    red and green with tone (lighter, darker, etc.)
    """
    weight_list = _prepare_weights_list(weights, value_name)
    _transform_weights_values(weight_list, value_name)
    _append_css_class_to_weights(weight_list, value_name)
    return weight_list


def _prepare_weights_list(weights, value_name='weight'):
    """
    Prepares list of weights from tree structure of weights and
    sorts them.
    """
    weight_list = []

    def _process(items):
        for item in items:
            if value_name in item and item[value_name] is not None:
                weight_list.append(item)
            if 'weights' in item:
                _process(item['weights'].values())
    _process(weights)
    weight_list.sort(key=lambda a: abs(a[value_name]))
    return weight_list


def _transform_weights_values(weight_list, value_name='weight',
                              transformed_value_name='transformed_weight'):
    """
    Adds transformed weight (as log of it) to each param weight item.
    """
    min_val = None
    for item in weight_list:
        val = item[value_name]
        if val == 0:
            item[transformed_value_name] = 0
        else:
            if min_val is None:
                min_val = val
            item[transformed_value_name] = math.log(abs(val / min_val))


def _append_css_class_to_weights(weight_list, value_name='weight',
                                 transformed_value_name='transformed_weight'):
    if weight_list and 'transformed_weight' in weight_list[-1]:
        max_transformed_val = weight_list[-1]['transformed_weight']
        delta = round(max_transformed_val / len(TONES))
        for i, tone in enumerate(TONES):
            limit = i * delta
            for item in weight_list:
                if abs(item[transformed_value_name]) >= limit:
                    color = 'green' if item[value_name] > 0 else 'red'
                    item['css_class'] = "%s %s" % (color, tone)
