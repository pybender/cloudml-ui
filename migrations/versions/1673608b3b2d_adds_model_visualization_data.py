"""adds Model.visualization_data

Revision ID: 1673608b3b2d
Revises: 4876f4a965f7
Create Date: 2015-01-18 12:52:26.851907

"""

# revision identifiers, used by Alembic.
revision = '1673608b3b2d'
down_revision = '4876f4a965f7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    from api.base.models import JSONType
    op.add_column('model', sa.Column('visualization_data', JSONType(), nullable=True))


def downgrade():
    op.drop_column('model', 'visualization_data')
