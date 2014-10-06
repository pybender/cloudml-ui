"""adding tags to xml import handlers

Revision ID: 1be8c3c69dee
Revises: 1932180aaf2b
Create Date: 2014-10-06 10:04:58.235748

"""

# revision identifiers, used by Alembic.
revision = '1be8c3c69dee'
down_revision = '1932180aaf2b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('handler_tag',
        sa.Column('xml_import_handler_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['xml_import_handler_id'], ['xml_import_handler.id'], onupdate='CASCADE', ondelete='CASCADE')
    )

def downgrade():
    op.drop_table('handler_tag')
