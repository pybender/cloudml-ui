"""weight_name_unlimited

Revision ID: 28e862da77e4
Revises: 9f760682819
Create Date: 2014-11-12 18:58:03.347796

"""

# revision identifiers, used by Alembic.
revision = '28e862da77e4'
down_revision = '9f760682819'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('weight', 'name', type_=sa.types.TEXT)


def downgrade():
    op.alter_column('weight', 'name', type_=sa.types.String(200))
