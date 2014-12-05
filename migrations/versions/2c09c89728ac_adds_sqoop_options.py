"""adds sqoop.options

Revision ID: 2c09c89728ac
Revises: 7d25aa6ef60
Create Date: 2014-12-05 17:42:06.733166

"""

# revision identifiers, used by Alembic.
revision = '2c09c89728ac'
down_revision = '7d25aa6ef60'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('xml_sqoop', sa.Column(
        'options', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('xml_sqoop', 'options')
