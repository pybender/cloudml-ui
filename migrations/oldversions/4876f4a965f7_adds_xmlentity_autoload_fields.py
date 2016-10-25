"""adds XmlEntity.autoload_fields

Revision ID: 4876f4a965f7
Revises: 35ab4adbcdd4
Create Date: 2015-01-12 15:26:11.864191

"""

# revision identifiers, used by Alembic.
revision = '4876f4a965f7'
down_revision = '35ab4adbcdd4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('xml_entity', sa.Column('autoload_fields', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('xml_entity', 'autoload_fields')
