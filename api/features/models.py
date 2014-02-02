import json
import logging

from sqlalchemy import event
from sqlalchemy.orm import deferred, undefer
from sqlalchemy.schema import CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from api.base.models import BaseModel, db, JSONType, S3File
from core.trainer.classifier_settings import CLASSIFIERS
from config import TRANSFORMERS, SCALERS, SYSTEM_FIELDS


class ExportImportMixin(object):
    """
    Mixin with methods to serialize/de-serialize model to JSON
    when import/export to file.
    """
    NO_PARAMS_KEY = False

    def from_dict(self, obj_dict, extra_fields={}, commit=True):
        obj_dict.update(extra_fields)
        fields_list = list(self.FIELDS_TO_SERIALIZE) + extra_fields.keys()

        for field in fields_list:
            if self.NO_PARAMS_KEY and field == 'params':
                # Fields that would be placed to params dict.
                params_fields = set(obj_dict.keys()) - \
                    set(self.FIELDS_TO_SERIALIZE + SYSTEM_FIELDS)
                value = dict([(name, obj_dict[name])
                             for name in params_fields])
            else:
                value = obj_dict.get(field, None)
            if value is not None:
                setattr(self, field, value)

        self.save(commit=commit)

    def to_dict(self):
        data = {}
        for field in self.FIELDS_TO_SERIALIZE:
            val = getattr(self, field, None)
            if val is not None:
                if self.NO_PARAMS_KEY and field == 'params':
                    for key, value in self.params.iteritems():
                        data[key] = value
                else:
                    field_type = getattr(
                        self.__class__, field).property.columns[0].type

                    if isinstance(field_type, db.Boolean) \
                            or isinstance(field_type, JSONType):
                        if not val:
                            continue

                    data[field] = val
        return data


### Predefined Items ###
class PredefinedItemMixin(object):
    name = db.Column(db.String(200), nullable=False, unique=True)

    @declared_attr
    def params(cls):
        return db.Column(JSONType)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__.lower(), self.type)


class NamedFeatureType(BaseModel, PredefinedItemMixin,
                       ExportImportMixin, db.Model):
    """ Represents named feature type """
    __tablename__ = 'predefined_feature_type'
    TYPES_LIST = ['boolean', 'int', 'float', 'numeric', 'date',
                  'map', 'categorical_label', 'categorical',
                  'text', 'regex', 'composite']
    FIELDS_TO_SERIALIZE = ('name', 'type', 'input_format', 'params')

    type = db.Column(
        db.Enum(*TYPES_LIST, name='named_feature_types'), nullable=False)
    input_format = db.Column(db.String(200))


class PredefinedClassifier(BaseModel, PredefinedItemMixin,
                           db.Model, ExportImportMixin):
    """ Represents predefined classifier """
    NO_PARAMS_KEY = False
    FIELDS_TO_SERIALIZE = ('type', 'params')

    TYPES_LIST = CLASSIFIERS.keys()
    type = db.Column(
        db.Enum(*TYPES_LIST, name='classifier_types'), nullable=False)


class PredefinedTransformer(BaseModel, PredefinedItemMixin, db.Model,
                            ExportImportMixin):
    """ Represents predefined feature transformer """
    FIELDS_TO_SERIALIZE = ('type', 'params')
    NO_PARAMS_KEY = False

    TYPES_LIST = TRANSFORMERS.keys()
    type = db.Column(
        db.Enum(*TYPES_LIST, name='transformer_types'), nullable=False)
    vocabulary = deferred(db.Column(S3File))
    vocabulary_size = db.Column(db.Integer, default=0)


class PredefinedScaler(BaseModel, PredefinedItemMixin, db.Model,
                       ExportImportMixin):
    """ Represents predefined feature scaler """
    FIELDS_TO_SERIALIZE = ('type', 'params')
    NO_PARAMS_KEY = False

    TYPES_LIST = SCALERS.keys()
    type = db.Column(
        db.Enum(*TYPES_LIST, name='scaler_types'), nullable=False)


### Feature and Feature Set models ###
class RefFeatureSetMixin(object):
    @declared_attr
    def feature_set_id(cls):
        return db.Column('feature_set_id',
                         db.ForeignKey('feature_set.id'))

    @declared_attr
    def feature_set(cls):
        return relationship("FeatureSet")


class Feature(ExportImportMixin, RefFeatureSetMixin,
              BaseModel, db.Model):
    FIELDS_TO_SERIALIZE = ('name', 'type', 'input_format', 'params',
                           'default', 'is_target_variable', 'is_required',
                           'transformer', 'scaler')

    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(200), nullable=False)
    input_format = db.Column(db.String(200))
    default = db.Column(JSONType)  # TODO: think about type
    is_required = db.Column(db.Boolean, default=True)
    is_target_variable = db.Column(db.Boolean, default=False)

    params = deferred(db.Column(JSONType, default={}))
    transformer = deferred(db.Column(JSONType))
    transformer_vocabulary = deferred(db.Column(S3File))
    transformer_vocabulary_size = db.Column(db.Integer)
    scaler = deferred(db.Column(JSONType))

    __table_args__ = (UniqueConstraint(
        'feature_set_id', 'name', name='name_unique'), )

    def __repr__(self):
        return '<Feature %s>' % self.name

    def transformer_type(self):
        if self.transformer is None:
            return None
        return self.transformer['type']

    def scaler_type(self):
        if self.scaler is None:
            return None
        return self.scaler['type']

    def save(self, commit=True):
        super(Feature, self).save(commit=False)
        if self.is_target_variable:
            Feature.query\
                .filter(
                    Feature.is_target_variable, Feature.name != self.name,
                    Feature.feature_set_id == self.feature_set_id)\
                .update({Feature.is_target_variable: False})
        if commit:
            db.session.commit()


class FeatureSet(ExportImportMixin, BaseModel, db.Model):
    """ Represents list of the features with schema name."""
    FIELDS_TO_SERIALIZE = ('schema_name', )

    FEATURES_STRUCT = {'schema_name': '',
                       'features': [],
                       "feature_types": []}
    schema_name = db.Column(db.String(200), nullable=False, default='noname')
    target_variable = db.Column(db.String(200))
    features_count = db.Column(db.Integer, default=0)
    features_dict = db.Column(JSONType)
    modified = db.Column(db.Boolean, default=False)
    __table_args__ = (
        CheckConstraint(features_count >= 0,
                        name='check_features_count_positive'), {})

    def __repr__(self):
        return '<Feature Set {0} ({1})>'.format(self.schema_name, self.target_variable)

    def _prepare_features_dict(self, features_dict):
        """
        Append saved fitted transformers to features dict if presented
        :param features_dict:
        :return:
        """
        features_db = {}
        features_query = Feature.query \
            .filter_by(feature_set=self) \
            .filter(Feature.transformer_vocabulary_size > 0) \
            .options(undefer('transformer_vocabulary'))
        for feature in features_query:
            features_db[feature.name] = (
                feature.transformer_vocabulary,
                feature.transformer_vocabulary_size)

        for feature in features_dict['features']:
            if not feature.get('transformer'):
                continue
            vocab, vocab_size = features_db[feature['name']] \
                if feature['name'] in features_db else (None, None)
            if vocab:
                if not 'params' in feature['transformer']:
                    feature['transformer']['params'] = {}
                feature['transformer']['params']['vocabulary'] =\
                    json.loads(vocab)
                logging.info('Saved vocabulary has been applied for '
                             'transformer {0} of feature {1}, size {2}'.format(
                    feature['transformer']['type'], feature['name'], vocab_size
                ))

        return features_dict

    @property
    def features(self):
        if self.modified:
            self.features_dict = self.to_dict()
            self.modified = False
            self.save()
        return self._prepare_features_dict(self.features_dict)

    def from_dict(self, features_dict, commit=True):
        self.schema_name = features_dict['schema_name']

        type_list = features_dict.get('feature_types', None)
        if type_list:
            for feature_type in type_list:
                count = NamedFeatureType.query.filter_by(name=feature_type['name']).count()
                if not count:
                    ntype = NamedFeatureType()
                    ntype.from_dict(feature_type, commit=False)

        for feature_dict in features_dict['features']:
            feature = Feature(feature_set=self)
            feature.from_dict(feature_dict, commit=False)
        if commit:
            db.session.commit()
            db.session.expire(self, ['target_variable',
                                        'features_count',
                                        'features_dict'])

    def to_dict(self):
        features_dict = {'schema_name': self.schema_name,
                         'features': [],
                         "feature_types": []}
        types = []
        for feature in Feature.query.filter_by(feature_set=self):
            if feature.type not in NamedFeatureType.TYPES_LIST:
                types.append(feature.type)
            features_dict['features'].append(feature.to_dict())

        for ftype in set(types):
            named_type = NamedFeatureType.query.filter_by(name=ftype).one()
            features_dict['feature_types'].append(named_type.to_dict())

        return features_dict

    def save(self, commit=True):
        # TODO: Why do default attr of the column not work?
        if self.features_dict is None:
            self.features_dict = self.FEATURES_STRUCT
        self.features_dict['schema_name'] = self.schema_name
        BaseModel.save(self, commit=commit)


@event.listens_for(Feature, "after_insert")
def after_insert_feature(mapper, connection, target):
    if target.feature_set is not None:
        update_feature_set_on_change_features(
            connection, target.feature_set, target)


@event.listens_for(Feature, "after_update")
def after_update_feature(mapper, connection, target):
    if target.feature_set is not None:
        update_feature_set_on_change_features(
            connection, target.feature_set, target)


@event.listens_for(Feature, "after_delete")
def after_delete_feature(mapper, connection, target):
    if target.feature_set is not None:
        update_feature_set_on_change_features(
            connection, target.feature_set, None)


def update_feature_set_on_change_features(connection, fset, feature):
    count = Feature.query.filter_by(feature_set=fset).count()
    values = {'features_count': count,
              'modified': True}
    if feature and feature.is_target_variable:
        values['target_variable'] = feature.name

    connection.execute(
        FeatureSet.__table__.update().
        where(FeatureSet.id == fset.id).values(**values))
