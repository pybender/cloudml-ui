"""adds Transformer.field_name and feature_type 

Revision ID: 2f078385306e
Revises: 2b00f038289b
Create Date: 2014-09-12 11:02:34.364825

"""

# revision identifiers, used by Alembic.
revision = '2f078385306e'
down_revision = '2b00f038289b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('transformer', sa.Column('feature_type', sa.String(length=100), nullable=True))
    op.add_column('transformer', sa.Column('field_name', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('transformer', 'field_name')
    op.drop_column('transformer', 'feature_type')
