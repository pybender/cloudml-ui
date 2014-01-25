"""rename_feature_require_field

Revision ID: 403e252f541d
Revises: None
Create Date: 2014-01-25 11:48:53.565872

"""

# revision identifiers, used by Alembic.
revision = '403e252f541d'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('feature', 'required', new_column_name='is_required')


def downgrade():
    op.alter_column('feature', 'is_required', new_column_name='required')
