"""empty message

Revision ID: 2cfac6f3a80e
Revises: 3e454e1e3715
Create Date: 2015-11-16 16:33:49.500471

"""

# revision identifiers, used by Alembic.
revision = '2cfac6f3a80e'
down_revision = None #'3e454e1e3715'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('data_set', sa.Column('locked', sa.Boolean(), default=False))
    op.add_column('model', sa.Column('locked', sa.Boolean(), default=False))
    op.add_column('feature_set', sa.Column('locked', sa.Boolean(), default=False))
    op.add_column('xml_import_handler', sa.Column('locked', sa.Boolean(), default=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('xml_import_handler', 'locked')
    op.drop_column('feature_set', 'locked')
    op.drop_column('model', 'locked')
    op.drop_column('data_set', 'locked')
    ### end Alembic commands ###