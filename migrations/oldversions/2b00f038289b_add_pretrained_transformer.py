"""add pretrained transformer

Revision ID: 2b00f038289b
Revises: 12bb341247df
Create Date: 2014-09-11 10:11:21.142447

"""

# revision identifiers, used by Alembic.
revision = '2b00f038289b'
down_revision = '12bb341247df'

from alembic import op
import sqlalchemy as sa


transformers_types = sa.Enum(
    'Count', 'Tfidf', 'Lda', 'Dictionary', 'Lsi',
    name='pretrained_transformer_types')
transformer_statuses = sa.Enum('New', 'Queued', 'Importing', 'Imported', 'Requesting Instance', 'Instance Started', 'Training', 'Trained', 'Error', 'Canceled', name='transformer_statuses')


def upgrade():
    from api.base.models import JSONType, S3File
    op.create_table('transformer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_on', sa.DateTime(), server_default='now()', nullable=True),
        sa.Column('updated_on', sa.DateTime(), server_default='now()', nullable=True),
        sa.Column('params', JSONType(), nullable=True),
        sa.Column('type', transformers_types, nullable=False),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('trainer', S3File(), nullable=True),
        sa.Column('status', transformer_statuses, nullable=True),
        sa.Column('trainer_size', sa.BigInteger(), nullable=True),
        sa.Column('trained_by_id', sa.Integer(), nullable=True),
        sa.Column('training_time', sa.Integer(), nullable=True),
        sa.Column('spot_instance_request_id', sa.String(length=100), nullable=True),
        sa.Column('train_import_handler_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('memory_usage', sa.Integer(), nullable=True),
        sa.Column('train_import_handler_type', sa.String(length=200), nullable=True),
        sa.Column('error', sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['trained_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('transformer_dataset',
        sa.Column('transformer_id', sa.Integer(), nullable=True),
        sa.Column('data_set_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['data_set_id'], ['data_set.id'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transformer_id'], ['transformer.id'], onupdate='CASCADE', ondelete='CASCADE')
    )

def downgrade():
    transformers_types.drop(op.get_bind(), checkfirst=False)
    transformer_statuses.drop(op.get_bind(), checkfirst=False)
    op.drop_table('transformer_dataset')
    op.drop_table('transformer')
