"""Add transformer_vocabulary_size to Feature

Revision ID: 1b7ebde23a53
Revises: 1388851afc4f
Create Date: 2014-02-02 23:12:44.301510

"""

# revision identifiers, used by Alembic.
revision = '1b7ebde23a53'
down_revision = '1388851afc4f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('feature', sa.Column('transformer_vocabulary_size', sa.Integer, default=0))


def downgrade():
    op.drop_column('feature', 'transformer_vocabulary_size')
