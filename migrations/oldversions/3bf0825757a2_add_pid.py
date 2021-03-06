"""Add pid

Revision ID: 3bf0825757a2
Revises: 4b8f9005cb69
Create Date: 2014-04-28 07:28:58.757568

"""

# revision identifiers, used by Alembic.
revision = '3bf0825757a2'
down_revision = '4b8f9005cb69'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cluster', sa.Column('pid', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cluster', 'pid')
    ### end Alembic commands ###
