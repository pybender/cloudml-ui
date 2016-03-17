"""adding model verification models

Revision ID: 3337863929da
Revises: 451a64d06984
Create Date: 2016-02-27 13:01:33.083488

"""

# revision identifiers, used by Alembic.
revision = '3337863929da'
down_revision = '451a64d06984'

from alembic import op
import sqlalchemy as sa


def upgrade():
    from api.base.models import JSONType
    op.create_table('server_model_verification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default='now()', nullable=True),
    sa.Column('updated_on', sa.DateTime(), server_default='now()', nullable=True),
    sa.Column('server_id', sa.Integer(), nullable=True),
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.Column('test_result_id', sa.Integer(), nullable=True),
    sa.Column('description', JSONType(), nullable=True),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('import_handler_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['import_handler_id'], ['xml_import_handler.id'], ),
    sa.ForeignKeyConstraint(['model_id'], ['model.id'], ),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], ),
    sa.ForeignKeyConstraint(['test_result_id'], ['test_result.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('verification_example',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('verification_id', sa.Integer(), nullable=True),
    sa.Column('example_id', sa.Integer(), nullable=True),
    sa.Column('result', JSONType(), nullable=True),
    sa.ForeignKeyConstraint(['example_id'], ['test_example.id'], ),
    sa.ForeignKeyConstraint(['verification_id'], ['server_model_verification.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('verification_example')
    op.drop_table('server_model_verification')
