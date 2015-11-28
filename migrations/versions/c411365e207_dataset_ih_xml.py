"""empty message

Revision ID: c411365e207
Revises: 88222ec90e4
Create Date: 2015-11-11 16:22:20.716551

"""

# revision identifiers, used by Alembic.
revision = 'c411365e207'
down_revision = '88222ec90e4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('data_set', sa.Column('import_handler_xml', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('data_set', 'import_handler_xml')
