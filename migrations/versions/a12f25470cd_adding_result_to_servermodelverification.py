"""adding result to ServerModelVerification

Revision ID: a12f25470cd
Revises: 3337863929da
Create Date: 2016-02-29 17:18:18.064475

"""

# revision identifiers, used by Alembic.
revision = 'a12f25470cd'
down_revision = '3337863929da'

from alembic import op
import sqlalchemy as sa


def upgrade():
    from api.base.models import JSONType
    op.add_column('server_model_verification', sa.Column('result', JSONType(), nullable=True))


def downgrade():
    op.drop_column('server_model_verification', 'result')