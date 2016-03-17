"""adding statuses and params_map to server_model_verification table

Revision ID: 2571339e92d6
Revises: a12f25470cd
Create Date: 2016-03-05 11:21:58.782477

"""

# revision identifiers, used by Alembic.
revision = '2571339e92d6'
down_revision = 'a12f25470cd'

from alembic import op
import sqlalchemy as sa

type_ = sa.Enum('New', 'Queued', 'In Progress', 'Error', 'Done', name='model_verification_statuses')


def upgrade():
    type_.create(op.get_bind(), checkfirst=False)

    from api.base.models import JSONType
    op.add_column('server_model_verification', sa.Column('error', sa.Text(), nullable=True))
    op.add_column('server_model_verification', sa.Column('params_map', JSONType(), nullable=True))
    op.add_column('server_model_verification', sa.Column('status', type_, nullable=False, server_default='New'))


def downgrade():
    op.drop_column('server_model_verification', 'status')
    op.drop_column('server_model_verification', 'params_map')
    op.drop_column('server_model_verification', 'error')
    type_.drop(op.get_bind(), checkfirst=False)
