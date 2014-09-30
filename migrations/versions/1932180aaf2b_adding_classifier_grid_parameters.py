"""adding classifier grid parameters

Revision ID: 1932180aaf2b
Revises: 26a159467f7a
Create Date: 2014-09-28 15:11:51.737460

"""

# revision identifiers, used by Alembic.
revision = '1932180aaf2b'
down_revision = '26a159467f7a'

from alembic import op
import sqlalchemy as sa


statuses = sa.Enum('New', 'Queued', 'Calculating', 'Completed',
                   name='classifier_grid_params_statuses')

def upgrade():
    from api.base.models import JSONType
    op.create_table('classifier_grid_params',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default='now()', nullable=True),
    sa.Column('updated_on', sa.DateTime(), server_default='now()', nullable=True),
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.Column('scoring', sa.String(length=100), nullable=True, default='accuracy'),
    sa.Column('train_data_set_id', sa.Integer(), nullable=True),
    sa.Column('test_data_set_id', sa.Integer(), nullable=True),
    sa.Column('status', statuses, nullable=True),
    sa.Column('parameters', JSONType(), nullable=True),
    sa.Column('parameters_grid', JSONType(), nullable=True),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['model_id'], ['model.id'], ),
    sa.ForeignKeyConstraint(['test_data_set_id'], ['data_set.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['train_data_set_id'], ['data_set.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('classifier_grid_params')
    statuses.drop(op.get_bind(), checkfirst=False)
