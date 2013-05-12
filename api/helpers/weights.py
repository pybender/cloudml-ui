import math
import re
from api import app


def calc_weights_css(weights, css_cls):
    """
    Determines tones of color dependly of weight value.
    """
    cmp_func = lambda a: abs(a['weight'])

    def get_min_no_zero(weights):
        no_zero_weights = [w for w in weights if w['weight'] != 0]
        return min(no_zero_weights, key=cmp_func)['weight']

    def normalize_weights(weights, min_weight):
        weights = [{'name': item['name'],
                    'weight': item['weight'],
                    'transformed_weight': math.log(
                        abs(item['weight'] / min_weight))
                    if item['weight'] != 0 else 0}
                   for item in weights]
        weights.sort(key=cmp_func)
        if min_weight > 0:
            weights.reverse()
        return weights

    min_weight = get_min_no_zero(weights)
    weights = normalize_weights(weights, min_weight)
    tones = ['lightest', 'lighter', 'light', 'dark', 'darker', 'darkest']
    tones_count = len(tones)
    cmp_func = lambda a: abs(a['transformed_weight'])
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


def weights2tree(weights):
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

            if not part in parent_node:
                parent_node[part] = {}

            parent_node = parent_node[part]
    return tree


def get_weighted_data(model, row):
    """
    Add weights and color tones to each test example parameter.
    """
    weights_dict = {}
    weight_list = app.db.Weight.find({'model_name': model.name})
    for weight in weight_list:
        # TODO: use -> in all parameters
        name = weight['name'].replace('->', '.')
        weights_dict[name] = weight

    result = {}
    for key, value in row.iteritems():
        result[key] = {'value': value}
        if key in weights_dict:
            wdict = weights_dict[key]
            result[key]['weight'] = wdict['value']
            result[key]['css_class'] = wdict['css_class']
        else:
            if isinstance(value, basestring):
                value = value.strip()
                # try to find weight for {{ key.value }}
                concated_key = ("%s.%s" % (key, value)).lower()
                if concated_key in weights_dict:
                    wdict = weights_dict[concated_key]
                    result[key]['weight'] = wdict['value']
                    result[key]['css_class'] = wdict['css_class']
                else:
                    # try to find each word from the value
                    rgx = re.compile("(\w[\w']*)")
                    words = rgx.findall(value)
                    result[key]['type'] = 'List'
                    for word in words:
                        word = word.lower().strip()
                        if not 'weights' in result[key]:
                            result[key]['weights'] = {}
                        concated_key = "%s.%s" % (key, word)
                        if concated_key in weights_dict:
                            wdict = weights_dict[concated_key]
                            word_weight = {'weight': wdict['value'],
                                           'css_class': wdict['css_class']}
                            result[key]['weights'][word] = word_weight
            elif isinstance(value, dict):
                result[key]['type'] = 'Dictionary'
                for dkey, dvalue in value.iteritems():
                    concated_key = ("%s.%s=%s" % (key, dkey, dvalue))
                    if not 'weights' in result[key]:
                        result[key]['weights'] = {}
                    if concated_key in weights_dict:
                        wdict = weights_dict[concated_key]
                        result[key]['weights'][dkey] = {'weight': wdict['value'],
                                                        'css_class': wdict['css_class'],
                                                        'value': dvalue}
    return result
