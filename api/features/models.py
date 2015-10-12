# Authors: Nikolay Melnik <nmelnik@upwork.com>

from sqlalchemy import event
from sqlalchemy.orm import deferred, backref
from sqlalchemy.schema import CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from api.base.models import BaseModel, db, JSONType
from cloudml.trainer.classifier_settings import CLASSIFIERS
from config import TRANSFORMERS, SCALERS, FIELDS_MAP, SYSTEM_FIELDS


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
            dict_field_name = FIELDS_MAP.get(field, field)
            if self.NO_PARAMS_KEY and field == 'params':
                # Fields that would be placed to params dict.
                params_fields = set(obj_dict.keys()) - \
                    set(self.FIELDS_TO_SERIALIZE + SYSTEM_FIELDS)
                value = dict([(name, obj_dict[name])
                             for name in params_fields])
            else:
                value = obj_dict.get(dict_field_name, None)
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

                    field_name = FIELDS_MAP.get(field, field)
                    data[field_name] = val
        return data


# ==== Predefined Items ====
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


class PredefinedScaler(BaseModel, PredefinedItemMixin, db.Model,
                       ExportImportMixin):
    """ Represents predefined feature scaler """
    FIELDS_TO_SERIALIZE = ('type', 'params')
    NO_PARAMS_KEY = False

    TYPES_LIST = SCALERS.keys()
    type = db.Column(
        db.Enum(*TYPES_LIST, name='scaler_types'), nullable=False)


# ==== Feature and Feature Set models ====
class RefFeatureSetMixin(object):
    @declared_attr
    def feature_set_id(cls):
        return db.Column('feature_set_id',
                         db.ForeignKey('feature_set.id'))

    @declared_attr
    def feature_set(cls):
        return relationship("FeatureSet", backref=backref('feature_list'))


class Feature(ExportImportMixin, RefFeatureSetMixin,
              BaseModel, db.Model):
    FIELDS_TO_SERIALIZE = ('name', 'type', 'input_format', 'params',
                           'default', 'is_target_variable', 'required',
                           'transformer', 'scaler', 'disabled')

    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(200), nullable=False)
    input_format = db.Column(db.String(200))
    default = db.Column(JSONType)  # TODO: think about type
    required = db.Column(db.Boolean, default=True)
    is_target_variable = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False, nullable=False,
                         server_default='false')

    params = deferred(db.Column(JSONType, default={}))
    transformer = deferred(db.Column(JSONType))
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

    @staticmethod
    def field_type_to_feature_type(field_type):
        if field_type == 'float' or field_type == 'boolean':
            return field_type
        elif field_type == 'integer':
            return 'int'
        elif field_type == 'string':
            return 'text'
        elif field_type is 'json':
            return 'map'
        else:
            return 'text'


class FeatureSet(ExportImportMixin, BaseModel, db.Model):
    """ Represents list of the features with schema name."""
    FIELDS_TO_SERIALIZE = ('schema_name', )

    FEATURES_STRUCT = {'schema-name': '',
                       'features': [],
                       "feature-types": []}
    schema_name = db.Column(db.String(200), nullable=False, default='noname')
    group_by = relationship('Feature', secondary=lambda: group_by_table,
                            backref='group_by_feature_set')
    target_variable = db.Column(db.String(200))
    features_count = db.Column(db.Integer, default=0)
    features_dict = db.Column(JSONType)
    modified = db.Column(db.Boolean, default=False)
    __table_args__ = (
        CheckConstraint(features_count >= 0,
                        name='check_features_count_positive'), {})

    def __repr__(self):
        return '<Feature Set {0} ({1})>'.format(
            self.schema_name, self.target_variable)

    @property
    def features(self):
        if self.features_dict is None or self.modified:
            self.features_dict = self.to_dict()
            self.modified = False
            self.save()
        return self.features_dict

    def from_dict(self, features_dict, commit=True):
        if features_dict is None or \
                not isinstance(features_dict, dict):
            raise ValueError('should be a dictionary')

        self.schema_name = features_dict['schema-name']
        self.group_by = []

        type_list = features_dict.get('feature-types', None)
        if type_list:
            for feature_type in type_list:
                count = NamedFeatureType.query.filter_by(
                    name=feature_type['name']).count()
                if not count:
                    ntype = NamedFeatureType()
                    ntype.from_dict(feature_type, commit=False)

        group_by_exist = 'group-by' in features_dict
        for feature_dict in features_dict['features']:
            feature = Feature(feature_set=self)
            feature.from_dict(feature_dict, commit=False)
            if group_by_exist and feature.name in features_dict['group-by']:
                self.group_by.append(feature)

        if commit:
            db.session.commit()
            db.session.expire(self, ['target_variable',
                                     'features_count',
                                     'features_dict'])

    def to_dict(self):
        features_dict = {'schema-name': self.schema_name,
                         'group-by': [f.name for f in self.group_by],
                         'features': [],
                         "feature-types": []}
        types = []
        for feature in Feature.query.filter_by(feature_set=self):
            if feature.type not in NamedFeatureType.TYPES_LIST:
                types.append(feature.type)
            features_dict['features'].append(feature.to_dict())

        for ftype in set(types):
            named_type = NamedFeatureType.query.filter_by(name=ftype).one()
            features_dict['feature-types'].append(named_type.to_dict())

        return features_dict

    def save(self, commit=True):
        # TODO: Why do default attr of the column not work?
        if self.features_dict is None:
            self.features_dict = self.FEATURES_STRUCT
        self.features_dict['schema-name'] = self.schema_name
        BaseModel.save(self, commit=commit)


group_by_table = db.Table(
    'group_by_table', db.Model.metadata,
    db.Column('feature_set_id', db.Integer, db.ForeignKey(
        'feature_set.id', ondelete='CASCADE', onupdate='CASCADE')),
    db.Column('feature_id', db.Integer, db.ForeignKey(
        'feature.id', ondelete='CASCADE', onupdate='CASCADE'))
)


@event.listens_for(Feature, "after_insert")
def after_insert_feature(mapper, connection, target):
    if target.feature_set is None and target.feature_set_id is not None:
        from sqlalchemy.orm import joinedload
        target = target.__class__.query.options(
            joinedload('feature_set')).get(target.id)
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
