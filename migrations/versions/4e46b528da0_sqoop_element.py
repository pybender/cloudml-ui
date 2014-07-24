"""sqoop element

Revision ID: 4e46b528da0
Revises: 264f08eeb00e
Create Date: 2014-04-10 23:52:16.558357

"""

# revision identifiers, used by Alembic.
revision = '4e46b528da0'
down_revision = '264f08eeb00e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('xml_sqoop',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target', sa.String(length=200), nullable=False),
        sa.Column('table', sa.String(length=200), nullable=False),
        sa.Column('where', sa.String(length=200), nullable=True),
        sa.Column('direct', sa.String(length=200), nullable=True),
        sa.Column('mappers', sa.String(length=200), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('datasource_id', sa.Integer(), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['datasource_id'], ['xml_data_source.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['entity_id'], ['xml_entity.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('xml_sqoop')
