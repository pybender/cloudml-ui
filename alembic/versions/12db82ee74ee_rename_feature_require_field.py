"""rename feature require field

Revision ID: 12db82ee74ee
Revises: 3173cd355cbc
Create Date: 2014-01-20 20:06:32.341146

"""

# revision identifiers, used by Alembic.
revision = '12db82ee74ee'
down_revision = '3173cd355cbc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('feature', 'required', new_column_name='is_required')


def downgrade():
    op.alter_column('feature', 'is_required', new_column_name='required')
