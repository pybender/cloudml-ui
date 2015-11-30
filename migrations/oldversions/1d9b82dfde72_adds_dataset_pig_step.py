"""adds DataSet.pig_step

Revision ID: 1d9b82dfde72
Revises: 17b60568b600
Create Date: 2014-12-20 15:19:40.754455

"""

# revision identifiers, used by Alembic.
revision = '1d9b82dfde72'
down_revision = '17b60568b600'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('data_set', sa.Column(
        'pig_step', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('data_set', 'pig_step')
