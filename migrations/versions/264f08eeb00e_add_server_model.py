"""Add Server model

Revision ID: 264f08eeb00e
Revises: 28da10c6b129
Create Date: 2014-02-18 16:15:13.398127

"""

# revision identifiers, used by Alembic.
revision = '264f08eeb00e'
down_revision = '23f079dfe4ee'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


def upgrade():
    op.create_table('server',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_on', sa.DateTime(), server_default='now()', nullable=True),
        sa.Column('updated_on', sa.DateTime(), server_default='now()', nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip', sa.String(length=200), nullable=False),
        sa.Column('folder', sa.String(length=600), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    servers_table = table('server',
        column('name', sa.String),
        column('ip', sa.String),
        column('folder', sa.String),
        column('is_default', sa.Boolean),
    )
    op.bulk_insert(servers_table,
        [
            {'name': 'analytics', 'ip': '127.0.0.1',
             'folder': 'odesk-match-cloudml/analytics', 'is_default': True},
        ]
    )


def downgrade():
    op.drop_table('server')
