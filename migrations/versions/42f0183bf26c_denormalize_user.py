"""denormalize user

Revision ID: f00d74e03bd
Revises: 403e252f541d
Create Date: 2014-01-25 11:48:58.978334

"""

# revision identifiers, used by Alembic.
revision = 'f00d74e03bd'
down_revision = '403e252f541d'

from alembic import op
import sqlalchemy as sa


TABLES = ['model', 'async_task', 'predefined_feature_type',
          'predefined_classifier', 'predefined_transformer',
          'predefined_scaler', 'feature', 'feature_set',
          'predefined_data_source', 'import_handler',
          'data_set', 'instance', 'test_result', 'test_example']


def upgrade():
    for tbl in TABLES:
        op.add_column(tbl, sa.Column('created_by_name', sa.String(length=200)))
        op.add_column(tbl, sa.Column('updated_by_name', sa.String(length=200)))

def downgrade():
    for tbl in TABLES:
        op.drop_column(tbl, 'created_by_name')
        op.drop_column(tbl, 'updated_by_name')
