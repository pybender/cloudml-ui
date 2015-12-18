"""support xml import handlers in models

Revision ID: 2fa7c91f4778
Revises: 330f04b3db02
Create Date: 2014-04-21 08:47:36.089742

"""

# revision identifiers, used by Alembic.
revision = '2fa7c91f4778'
down_revision = '330f04b3db02'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'model', sa.Column(
            'test_import_handler_type', sa.String(length=200),
            nullable=True, server_default='json'))
    op.add_column(
        'model', sa.Column(
            'train_import_handler_type', sa.String(length=200),
            nullable=True, server_default='json'))
    op.drop_constraint("model_test_import_handler_id_fkey", "model")
    op.drop_constraint("model_ttrain_import_handler_id_fkey", "model")


def downgrade():
    op.create_foreign_key(
        "model_test_import_handler_id_fkey", "model",
        "import_handler", ["test_import_handler_id"], ["id"])
    op.create_foreign_key(
        "model_ttrain_import_handler_id_fkey", "model",
        "import_handler", ["train_import_handler_id"], ["id"])
    op.drop_column('model', 'train_import_handler_type')
    op.drop_column('model', 'test_import_handler_type')
