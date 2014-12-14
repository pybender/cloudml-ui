"""add_memory_size_to_server

Revision ID: 3b38bc20aede
Revises: 2c09c89728ac
Create Date: 2014-12-10 13:56:46.239320

"""

# revision identifiers, used by Alembic.
revision = '3b38bc20aede'
down_revision = '2c09c89728ac'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'server', sa.Column('memory_mb', sa.Integer(),
                            server_default='0'))


def downgrade():
    op.drop_column('server', 'memory_mb')
