"""adds Test.weights_filled

Revision ID: 5adcc1a31357
Revises: aeb5a592587
Create Date: 2014-11-08 11:23:21.522419

"""

# revision identifiers, used by Alembic.
revision = '5adcc1a31357'
down_revision = 'aeb5a592587'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column(
        'test_result',
        sa.Column('fill_weights', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('test_result', 'fill_weights')
