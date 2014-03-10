"""generic fk to import handlers from models

Revision ID: 111b32f9fe34
Revises: 23f079dfe4ee
Create Date: 2014-03-10 15:06:35.716441

"""

# revision identifiers, used by Alembic.
revision = '111b32f9fe34'
down_revision = '23f079dfe4ee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('model', sa.Column('test_import_handler_type', sa.String(length=10), nullable=True))
    op.add_column('model', sa.Column('train_import_handler_type', sa.String(length=10), nullable=True))
    op.drop_constraint("model_test_import_handler_id_fkey", "model")
    op.drop_constraint("model_train_import_handler_id_fkey", "model")

def downgrade():
    op.drop_column('model', 'train_import_handler_type')
    op.drop_column('model', 'test_import_handler_type')
    op.create_foreign_key(
        "model_test_import_handler_id_fkey", "model",
        "import_handler", ["test_import_handler_id"], ["id"])
    op.create_foreign_key(
        "model_ttrain_import_handler_id_fkey", "model",
        "import_handler", ["train_import_handler_id"], ["id"])