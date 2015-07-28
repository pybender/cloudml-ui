# Authors: Nikolay Melnik <nmelnik@upwork.com>

from cloudml.trainer.scalers import SCALERS
from cloudml.trainer.transformers import TRANSFORMERS
from cloudml.trainer.classifier_settings import CLASSIFIERS


SYSTEM_FIELDS = ('name', 'created_on', 'updated_on', 'created_by',
                 'updated_by', 'type', 'is_predefined', 'feature_set')

FIELDS_MAP = {'input_format': 'input-format',
              'is_target_variable': 'is-target-variable',
              'required': 'is-required',
              'schema_name': 'schema-name'}
