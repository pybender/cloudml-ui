"""adding group_by to feature set

Revision ID: 12b83514c18
Revises: 36b19a6a2d96
Create Date: 2014-06-02 14:34:10.871478

"""

# revision identifiers, used by Alembic.
revision = '12b83514c18'
down_revision = '36b19a6a2d96'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('group_by_table',
    sa.Column('feature_set_id', sa.Integer(), nullable=True),
    sa.Column('feature_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['feature_id'], ['feature.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['feature_set_id'], ['feature_set.id'], onupdate='CASCADE', ondelete='CASCADE')
    )

def downgrade():
    op.drop_table('group_by_table')
