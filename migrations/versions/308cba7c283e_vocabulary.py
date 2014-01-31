"""empty message

Revision ID: 308cba7c283e
Revises: 36ddee11cad
Create Date: 2014-01-31 00:34:42.748767

"""

# revision identifiers, used by Alembic.
from api.base.models import S3File

revision = '308cba7c283e'
down_revision = '36ddee11cad'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('feature', sa.Column('transformer_vocabulary', S3File, nullable=True))
    op.add_column('predefined_transformer', sa.Column('vocabulary', S3File, nullable=True))


def downgrade():
    op.drop_column('predefined_transformer', 'vocabulary')
    op.drop_column('feature', 'transformer_vocabulary')
