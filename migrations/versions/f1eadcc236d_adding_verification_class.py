"""Adding verification class

Revision ID: f1eadcc236d
Revises: 2571339e92d6
Create Date: 2016-03-20 13:14:48.852315

"""

# revision identifiers, used by Alembic.
revision = 'f1eadcc236d'
down_revision = '2571339e92d6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('server_model_verification', sa.Column('clazz', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('server_model_verification', 'clazz')
