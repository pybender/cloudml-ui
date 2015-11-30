"""adds pig related fields to XmlQuery

Revision ID: 35ab4adbcdd4
Revises: 5ae37b823e80
Create Date: 2015-01-10 13:59:48.913472

"""

# revision identifiers, used by Alembic.
revision = '35ab4adbcdd4'
down_revision = '5ae37b823e80'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('xml_query', sa.Column('autoload_sqoop_dataset', sa.Boolean(), nullable=True))
    op.add_column('xml_query', sa.Column('sqoop_dataset_name', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('xml_query', 'sqoop_dataset_name')
    op.drop_column('xml_query', 'autoload_sqoop_dataset')
