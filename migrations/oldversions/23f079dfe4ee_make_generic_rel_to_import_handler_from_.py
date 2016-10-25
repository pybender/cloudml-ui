"""make generic rel to import handler from dataset

Revision ID: 23f079dfe4ee
Revises: 3c341eb62429
Create Date: 2014-03-10 09:25:09.091797

"""

# revision identifiers, used by Alembic.
revision = '23f079dfe4ee'
down_revision = '3c341eb62429'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'data_set',
        sa.Column('import_handler_type', sa.String(length=200), default="json")
    )
    op.drop_constraint("data_set_import_handler_id_fkey", "data_set")


def downgrade():
    op.drop_column('data_set', 'import_handler_type')
    op.create_foreign_key(
        "data_set_import_handler_id_fkey", "data_set",
        "import_handler", ["import_handler_id"], ["id"])
