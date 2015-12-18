"""add_trainer_size_field

Revision ID: 1cb1aef8263f
Revises: None
Create Date: 2014-02-13 06:49:19.612628

"""

# revision identifiers, used by Alembic.
revision = '1cb1aef8263f'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('model', sa.Column('trainer_size', sa.Integer, default=0))


def downgrade():
    op.drop_column('model', 'trainer_size')
