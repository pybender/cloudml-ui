"""Add_segment

Revision ID: 323f586eb1f5
Revises: 12b83514c18
Create Date: 2014-06-14 08:16:09.665046

"""

# revision identifiers, used by Alembic.
revision = '323f586eb1f5'
down_revision = '12b83514c18'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('segment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('records', sa.Integer(), nullable=True),
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['model_id'], ['model.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
  
    op.add_column(u'weight', sa.Column('segment_id', sa.Integer(), nullable=True))
    op.add_column(u'weights_category', sa.Column('segment_id', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'weights_category', 'segment_id')
    op.drop_column(u'weight', 'segment_id')
    op.drop_table('segment')
    ### end Alembic commands ###
