"""Add vocabulary_size

Revision ID: 1388851afc4f
Revises: 308cba7c283e
Create Date: 2014-01-31 17:53:17.131722

"""

# revision identifiers, used by Alembic.
revision = '1388851afc4f'
down_revision = '308cba7c283e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('predefined_transformer', sa.Column('vocabulary_size', sa.Integer, default=0))


def downgrade():
    op.drop_column('predefined_transformer', 'vocabulary_size')
