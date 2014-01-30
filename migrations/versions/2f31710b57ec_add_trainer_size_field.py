"""Add trainer_size field

Revision ID: 2f31710b57ec
Revises: 425f54281caa
Create Date: 2014-01-29 23:58:54.456063

"""

# revision identifiers, used by Alembic.
revision = '2f31710b57ec'
down_revision = '425f54281caa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('model', sa.Column('trainer_size', sa.Integer, default=0))


def downgrade():
    op.drop_column('model', 'trainer_size')
