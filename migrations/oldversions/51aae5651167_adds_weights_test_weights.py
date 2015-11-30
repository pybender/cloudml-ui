"""Adds Weights.test_weights

Revision ID: 51aae5651167
Revises: ddbec2c2fe4
Create Date: 2014-10-26 10:26:49.426275

"""

# revision identifiers, used by Alembic.
revision = '51aae5651167'
down_revision = 'ddbec2c2fe4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    from api.base.models import JSONType
    op.add_column('weight', sa.Column('test_weights', JSONType(), nullable=True))


def downgrade():
    op.drop_column('weight', 'test_weights')
