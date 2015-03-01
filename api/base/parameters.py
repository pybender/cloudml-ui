# parameters parser
from api.base.resources import ValidationError
from api.base.utils import isint, isfloat


def convert_auto_dict(val, c):
    import ast
    #if val != 'auto':
    return val


def convert_int_float_string_none(val, config):
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


TYPE_CONVERTORS = {
    'string': lambda a, c: a,
    'boolean': lambda a, c: a in ('True', 1, True),
    'float': lambda a, c: float(a),
    'integer': lambda a, c: int(a),
    'auto_dict': convert_auto_dict,
    'int_float_string_none': convert_int_float_string_none
}


def convert_parameters(config, params):
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
            if type_ in ('string', 'integer', 'float') and choices:
                check_choices(name, params[name], choices)
    return params


def check_choices(name, val, choices):
    if choices:
        if not val in choices:
            raise ValidationError(
                'Invalid {0}: should be one of {1}'.format(
                    name, ','.join(choices)))
