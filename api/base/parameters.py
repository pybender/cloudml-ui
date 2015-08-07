"""
Utility methods for parameters parsersing and converting.

Notes
-----
This methods mainly used for converting classifier's parameters
to corresponding type. This type specified in the classifier
config.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.base.resources import ValidationError
from api.base.utils import isint, isfloat


__all__ = ["convert_parameters"]


def convert_auto_dict(val, c):
    """
    TODO: Add support of the params like
    class_weight : {dict, auto}, optional in sklearn.svm.SVC
    """
    return val


def convert_int_float_string_none(val, config):
    """
    Parses parameter that could be int, float, string or none.
    A sample of this is max_features in Decision Tree Classifier.
    """
    if not val:
        return None

    if isint(val):
        return int(val)
    elif isfloat(val):
        return float(val)
    else:  # string
        choices = config.get('choices')
        if choices:
            check_choices(config.get('name'), val, choices)

    return val


def convert_float_or_int(val, config):
    if isint(val):
        return int(val)
    elif isfloat(val):
        return float(val)
    else:
        raise ValidationError(
            'Invalid value {0} for type {1}'.format(
                val, config.type))


TYPE_CONVERTORS = {
    'string': lambda a, c: a,
    'boolean': lambda a, c: a in ('True', 1, True, 'true'),
    'float': lambda a, c: float(a),
    'integer': lambda a, c: int(a),
    'auto_dict': convert_auto_dict,
    'int_float_string_none': convert_int_float_string_none,
    'float_or_int': convert_float_or_int
}


def convert_parameters(config, params):
    """
    Tries to convert the parameter value to corresponding type.

    Parameters
    ----------
    C : dict
        parameter's config with info about type, wheither it's required, etc.
    params: dict
        parameters filled by user
    """
    missed_params = []
    for param_config in config:
        if param_config.get('required', None) and \
                param_config['name'] not in params:
            missed_params.append(param_config['name'])
    if missed_params:
        raise ValidationError(
            'These params are required: {}'.format(
                ', '.join(missed_params))
        )

    for param_config in config:
        name = param_config.get('name')
        if name in params:
            type_ = param_config.get('type')
            convertor = TYPE_CONVERTORS[type_]
            try:
                params[name] = convertor(params[name], param_config)
            except ValueError, exc:
                raise ValidationError(
                    'Invalid parameter %s value: %s' % (name, exc))

            choices = param_config.get('choices')
            if choices:
                check_choices(name, params[name], choices)
    return params


def check_choices(name, val, choices):
    if choices:
        if val not in choices:
            raise ValidationError(
                'Invalid {0}: should be one of {1}'.format(
                    name, ','.join(choices)))
