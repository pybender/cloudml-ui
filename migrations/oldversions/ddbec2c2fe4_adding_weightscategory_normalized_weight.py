"""adding WeightsCategory.normalized_weight

Revision ID: ddbec2c2fe4
Revises: 1932180aaf2b
Create Date: 2014-10-24 13:13:25.895784

"""

# revision identifiers, used by Alembic.
revision = 'ddbec2c2fe4'
down_revision = '1932180aaf2b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column(
        'weights_category',
        sa.Column('normalized_weight', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('weights_category', 'normalized_weight')
