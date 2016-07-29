from api.features.models import Feature, FeatureSet
from api import app
__all__ = ['update_target_variable']


def update_target_variable():
    """Sets feature target variable where it's absent, but set in FeatureSet"""
    db = app.sql_db
    features_sets = FeatureSet.query.all()
    for fs in features_sets:
        if fs.target_variable:
            Feature.query.filter(Feature.feature_set_id == fs.id)\
                .filter(Feature.name == fs.target_variable)\
                .filter(Feature.is_target_variable is not True)\
                .update({Feature.is_target_variable: True})
    db.session.commit()
    print "Done"
