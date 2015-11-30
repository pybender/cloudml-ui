"""Adds DataSet.pig_row

Revision ID: 5ae37b823e80
Revises: d0e4cbfaa5c
Create Date: 2014-12-26 12:11:27.537386

"""

# revision identifiers, used by Alembic.
revision = '5ae37b823e80'
down_revision = 'd0e4cbfaa5c'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    from api.base.models import JSONType
    op.add_column('data_set', sa.Column('pig_row', JSONType(), nullable=True))


def downgrade():
    op.drop_column('data_set', 'pig_row')
