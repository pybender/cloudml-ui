"""adding WeightsCategory.class_label

Revision ID: 190872916592
Revises: 51aae5651167
Create Date: 2014-10-28 09:30:17.890159

"""

# revision identifiers, used by Alembic.
revision = '190872916592'
down_revision = '51aae5651167'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('weights_category', sa.Column(
        'class_label', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('weights_category', 'class_label')
