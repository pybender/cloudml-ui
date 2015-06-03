"""
Utils that used in model specific celery tasks.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import logging

from api.ml_models.models import Weight, WeightsCategory


def fill_model_weights(model, segment, class_label, weights):
    """
    Adds weights for specific class, also adds new categories not found
    in `categories_names`

    model: Model object
        model for what it needed to fill weights.
    segment: Segment object
        model segment
    class_label: string
    weights: dict
        Dictionary of the weights

    :param class_label: class_label of the weights to process
    :return:
    """
    from collections import defaultdict
    tree = defaultdict(dict)  # weights tree
    tree['weights'] = []
    categories_names = []
    w_added = 0
    cat_added = 0
    logging.info("Filling model {0} weights for segment {1} and "
                 "class {2}".format(model.name, segment.name, class_label))

    # Generating weights list with normalized weights and css classes
    # for them.
    from api.ml_models.helpers.weights import calc_weights_css
    positive_weights = calc_weights_css(weights['positive'], 'green')
    negative_weights = calc_weights_css(weights['negative'], 'red')
    weight_list = positive_weights + negative_weights
    weight_list.sort(key=lambda a: abs(a['weight']))
    weight_list.reverse()

    # Adding weights and weights categories to db
    for weight in weight_list:
        name = weight['name']
        splitted_name = name.split('->')
        long_name = ''
        count = len(splitted_name)
        current = tree
        for i, sname in enumerate(splitted_name):
            parent = long_name
            long_name = '%s.%s' % (long_name, sname) \
                if long_name else sname
            if i == (count - 1):
                # The leaf of the split (last element) is not a category,
                # it is the actual weight
                new_weight = Weight(
                    name=weight['name'], value=weight['weight'],
                    value2=weight['feature_weight'], parent=parent,
                    is_positive=bool(weight['weight'] > 0),
                    css_class=weight['css_class'], model=model,
                    segment=segment, class_label=str(class_label),
                    short_name=sname[0:199])
                new_weight.save(commit=False)
                w_added += 1

                current['weights'].append(new_weight)
            else:
                # Intermediate elements of the split, are actual categories
                # except of the last one (which is the actual weight)
                if long_name not in categories_names:
                    # Adding a category, if it has not already added
                    categories_names.append(long_name)
                    category = WeightsCategory(
                        name=long_name, parent=parent, short_name=sname,
                        model=model, segment=segment,
                        class_label=str(class_label))
                    category.save(commit=False)
                    cat_added += 1
                    current['subcategories'][sname] = {
                        'category': category,
                        'weights': [],
                        'subcategories': {}}
                current = current['subcategories'][sname]

    calc_tree_item(tree['subcategories'])
    return cat_added, w_added


def calc_tree_item(tree_item, parent=None):
    """
    Calculating categories normalized weight
    """
    for category_name, item in tree_item.iteritems():
        if 'category' in item:
            category = item['category']
            normalized_weight = 0
            for w in item['weights']:
                normalized_weight += w.value2
                w.category = category
            category.normalized_weight = normalized_weight
            if parent:
                parent.normalized_weight += normalized_weight
            if 'subcategories' in item:
                calc_tree_item(item['subcategories'], category)
