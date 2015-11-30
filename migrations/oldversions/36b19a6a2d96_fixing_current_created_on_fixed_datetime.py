"""fixing_current_created_on_fixed_datetime

Revision ID: 36b19a6a2d96
Revises: 3bf0825757a2
Create Date: 2014-05-29 13:51:19.424784

"""

# revision identifiers, used by Alembic.
revision = '36b19a6a2d96'
down_revision = '3bf0825757a2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('xml_import_handler', 'created_on', 
        server_default=sa.func.now(), nullable=True)
    op.alter_column('xml_import_handler', 'updated_on', 
        server_default=sa.func.now(), nullable=True)

    op.alter_column('cluster', 'created_on', 
        server_default=sa.func.now(), nullable=True)
    op.alter_column('cluster', 'updated_on', 
        server_default=sa.func.now(), nullable=True)

    op.alter_column('server', 'created_on', 
        server_default=sa.func.now(), nullable=True)
    op.alter_column('server', 'updated_on', 
        server_default=sa.func.now(), nullable=True)

def downgrade():
    pass
