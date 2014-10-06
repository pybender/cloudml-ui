"""Adding Tag.handler_count

Revision ID: 4cf7b204cad1
Revises: 1be8c3c69dee
Create Date: 2014-10-06 10:41:52.200001

"""

# revision identifiers, used by Alembic.
revision = '4cf7b204cad1'
down_revision = '1be8c3c69dee'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('tag', sa.Column('handlers_count', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('tag', 'handlers_count')
