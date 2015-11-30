"""adds Cluster.logs_folder

Revision ID: 17b60568b600
Revises: 3b38bc20aede
Create Date: 2014-12-20 14:54:43.596348

"""

# revision identifiers, used by Alembic.
revision = '17b60568b600'
down_revision = '3b38bc20aede'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('cluster', sa.Column(
        'logs_folder', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('cluster', 'logs_folder')
