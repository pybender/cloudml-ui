import re


def convert_name(name, to_text=False):
    """
    FeatureSet -> features_set
    FeatureSet -> Feature Set (if to_text)
    """
    if to_text:
        return re.sub("([a-z])([A-Z])", "\g<1> \g<2>", name)

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
