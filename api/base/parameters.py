"""
Utility methods for parameters parsersing and converting
to the type, which is specified in the config.

Notes
-----

Now it used for processing parameters of"

 * Model classifiers
 * Feature scalers
 * Feature transformers
 * Xml Import Handlers DataSources

"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api.base.resources import ValidationError
from cloudml.utils import isint, isfloat


__all__ = ["convert_parameters"]


def convert_parameters(config, params):
    """
    Tries to convert the parameter value to corresponding type.

    Parameters
    ----------
    C : dict
        parameter's config with info about type, wheither it's required, etc.
    params : dict
        parameters filled by user

    Note: Use `ParametersConvertorMixin` for converting parameters in forms.
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
            if params[name] is None:
                params.pop(name)
                continue
            try:
                params[name] = convertor(params[name], param_config)
            except ValueError, exc:
                raise ValidationError(
                    'Invalid parameter %s value: %s' % (name, exc))

            choices = param_config.get('choices')
            if choices and type_ == 'string':
                check_choices(name, params[name], choices)
    return params

# Convertors by the type


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

    if not '.' in str(val) and isint(val):
        return int(val)
    elif isfloat(val):
        return float(val)
    else:  # string
        choices = config.get('choices')
        if choices:
            check_choices(config.get('name'), val, choices)

    return val


def convert_float_or_int(val, config):
    if not '.' in str(val) and isint(val):
        return int(val)
    elif isfloat(val):
        return float(val)
    else:
        raise ValidationError(
            'Invalid value {0} for type {1}'.format(
                val, config.type))


def convert_string_list_none(val, config):
    if isinstance(val, dict):
        type_ = val.get('type')
        value = val.get('value')
        if type_ == 'empty':
            return None
        else:
            if config.get('required', None) and value is None:
                raise ValidationError(
                    '{0} parameter is required'.format(config.name))
            if type_ == 'string':
                return str(value) or ''
            elif type_ == 'list':
                if not isinstance(value, (list, tuple)):
                    return [value, ]
                return value
    else:
        if val is None or isinstance(val, basestring) or \
                isinstance(val, (list, tuple)):
            return val

    raise ValidationType(
        "Invalid subtype of the {0} parameter".format(config.name))


TYPE_CONVERTORS = {
    'string': lambda a, c: a,
    'boolean': lambda a, c: a in ('True', 1, True, 'true'),
    'float': lambda a, c: float(a),
    'integer': lambda a, c: int(a),
    'auto_dict': convert_auto_dict,
    'int_float_string_none': convert_int_float_string_none,
    'float_or_int': convert_float_or_int,
    'string_list_none': convert_string_list_none,
}

# Utils


def check_choices(name, val, choices):
    if choices:
        if val not in choices:
            raise ValidationError(
                'Invalid {0}: should be one of {1}'.format(
                    name, ','.join(choices)))
