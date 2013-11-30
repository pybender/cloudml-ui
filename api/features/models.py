from sqlalchemy.orm import deferred
from sqlalchemy.schema import CheckConstraint
from sqlalchemy import (Integer, String, Binary, Column,
                        Enum, ForeignKey)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from api.base.models import BaseModel, db, BasePredefinedItemModel
from api.db import JSONType
from core.trainer.classifier_settings import CLASSIFIERS
from config import TRANSFORMERS, SCALERS, FIELDS_MAP, SYSTEM_FIELDS


class ExportImportMixin(object):
    @classmethod
    def from_dict(cls, obj_dict, extra_fields={},
                  filter_params=None, save=True, add_new=False):
        obj_dict.update(extra_fields)
        fields_list = list(cls.FIELDS_TO_SERIALIZE) + extra_fields.keys()
        obj = None
        if not add_new and save:
            if filter_params is None:
                filter_params = {'name': obj_dict['name']}
            obj = cls.find_one(filter_params)

        if not obj:
            obj = cls()
            for field in fields_list:
                dict_field_name = FIELDS_MAP.get(field, field)
                if cls.NO_PARAMS_KEY and field == 'params':
                    # Fields that would be placed to params dict.
                    params_fields = set(obj_dict.keys()) - \
                        set(cls.FIELDS_TO_SERIALIZE + SYSTEM_FIELDS)
                    value = dict([(name, obj_dict[name])
                                 for name in params_fields])
                else:
                    value = obj_dict.get(dict_field_name, None)
                if value is not None:
                    obj[field] = value
            if save:
                obj.save()

            return obj, True

        return obj, False

    def to_dict(self):
        data = {}
        for field in self.FIELDS_TO_SERIALIZE:
            field_type = self.structure[field]
            val = self.get(field, None)
            if val is not None:
                if field_type in (bool, dict) and not val:
                    continue
                if self.NO_PARAMS_KEY and field == 'params':
                    for key, value in self.params.iteritems():
                        data[key] = value
                else:
                    field_name = FIELDS_MAP.get(field, field)
                    data[field_name] = val
        return data


### Predefined Items ###

class NamedFeatureType(BasePredefinedItemModel, db.Model):
    """ Represents named feature type """
    TYPES_LIST = ['boolean', 'int', 'float', 'numeric', 'date',
                  'map', 'categorical_label', 'categorical',
                  'text', 'regex', 'composite']

    type_ = Column(Enum(*TYPES_LIST, name='named_feature_types'))
    input_format = Column(String)


class PredefinedClassifier(BasePredefinedItemModel, db.Model):
    """ Represents predefined classifier """

    TYPES_LIST = CLASSIFIERS.keys()
    type_ = Column(Enum(*TYPES_LIST, name='classifier_types'))


class PredefinedTransformer(BasePredefinedItemModel, db.Model):
    """ Represents predefined feature transformer """

    TYPES_LIST = TRANSFORMERS.keys()
    type_ = Column(Enum(*TYPES_LIST, name='transformer_types'))


class PredefinedScaler(BasePredefinedItemModel, db.Model):
    """ Represents predefined feature scaler """

    TYPES_LIST = SCALERS.keys()
    type_ = Column(Enum(*TYPES_LIST, name='scaler_types'))


### Feature and Feature Set models ###

class Feature_Set(ExportImportMixin, BaseModel, db.Model):
    """ Represents list of the features with schema name."""
    schema_name = Column(String(200), nullable=False)
    target_variable = Column(String(200))
    features_count = Column(Integer)
    __table_args__ = (
        CheckConstraint(features_count >= 0,
                        name='check_features_count_positive'), {})

    def import_from_json(cls, features_dict):
        features_set = cls()
        features_set.schema_name = features_dict.get('schema-name', 'noname')
        features_set.save()

        for feature_type in features_dict.get('feature-types', []):
            NamedFeatureType.from_dict(feature_type)

        for feature_dict in features_dict.get('features', []):
            Feature.from_dict(
                feature_dict, add_new=True,
                extra_fields={'features_set': features_set})

        return features_set


class RefFeatureSetMixin(object):
    @declared_attr
    def feature_set_id(cls):
        return Column('feature_set_id', ForeignKey('feature_set.id'))

    @declared_attr
    def feature_set(cls):
        return relationship("FeatureSet")


class Feature(ExportImportMixin, RefFeatureSetMixin,
              BaseModel, db.Model):
    name = Column(String(200), nullable=False)
    type = Column(String(200))
    input_format = Column(String(200))
    default = Column(String(200))  # TODO: think about type
    required = Column(Binary)
    is_target_variable = Column(Binary)

    params = deferred(Column(JSONType))
    transformer = deferred(Column(JSONType))
    scaler = deferred(Column(JSONType))

    def transformer_type(self):
        if self.transformer is None:
            return None
        return self.transformer['type']

    def scaler_type(self):
        if self.scaler is None:
            return None
        return self.scaler['type']
