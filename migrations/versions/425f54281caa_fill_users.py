"""fill users

Revision ID: 425f54281caa
Revises: f00d74e03bd
Create Date: 2014-01-25 12:07:23.837468

"""

# revision identifiers, used by Alembic.
revision = '425f54281caa'
down_revision = 'f00d74e03bd'

from alembic import op
import sqlalchemy as sa
from api import app

db = app.sql_db


def upgrade():
    from api.ml_models.models import Model
    from api.async_tasks.models import AsyncTask
    from api.features.models import NamedFeatureType, PredefinedTransformer, PredefinedClassifier, PredefinedScaler, Feature, FeatureSet
    from api.import_handlers.models import PredefinedDataSource, ImportHandler, DataSet
    from api.instances.models import Instance
    from api.model_tests.models import TestResult, TestExample
    TABLES = [Model, AsyncTask, NamedFeatureType,
              PredefinedClassifier, PredefinedTransformer,
              PredefinedScaler, Feature, FeatureSet,
              PredefinedDataSource, ImportHandler,
              DataSet, Instance, TestResult, TestExample]
    for tbl in TABLES:
        for model in tbl.query.all():
            if model.created_by:
                model.created_by_name = "{} ({})".format(model.created_by.name, model.created_by.uid)
            if model.updated_by:
                model.updated_by_name = "{} ({})".format(model.updated_by.name, model.updated_by.uid)
            db.session.add(model)
    db.session.commit()

def downgrade():
    pass
