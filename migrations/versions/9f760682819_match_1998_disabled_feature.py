"""MATCH_1998_disabled_feature

Revision ID: 9f760682819
Revises: aeb5a592587
Create Date: 2014-11-09 11:53:02.442243

"""

# revision identifiers, used by Alembic.
revision = '9f760682819'
down_revision = 'aeb5a592587'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('feature', sa.Column('disabled', sa.Boolean, nullable=False,
                                       server_default='false'))


def downgrade():
    op.drop_column('feature', 'disabled')
