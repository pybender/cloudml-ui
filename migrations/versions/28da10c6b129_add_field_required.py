"""empty message

Revision ID: 28da10c6b129
Revises: 111b32f9fe34
Create Date: 2014-03-20 00:14:11.711892

"""

# revision identifiers, used by Alembic.
revision = '28da10c6b129'
down_revision = '111b32f9fe34'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('xml_field', sa.Column('required', sa.Boolean(),
                                         nullable=True, default=True))


def downgrade():
    op.drop_column('xml_field', 'required')
