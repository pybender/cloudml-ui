"""adding multipart to field

Revision ID: 330f04b3db02
Revises: 4e46b528da0
Create Date: 2014-04-18 08:16:38.623481

"""

# revision identifiers, used by Alembic.
revision = '330f04b3db02'
down_revision = '4e46b528da0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('xml_field', sa.Column(
        'multipart', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('xml_field', 'multipart')
