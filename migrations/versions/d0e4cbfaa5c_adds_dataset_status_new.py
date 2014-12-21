"""adds Dataset.status 'New'

Revision ID: d0e4cbfaa5c
Revises: 1d9b82dfde72
Create Date: 2014-12-21 13:29:06.298661

"""

# revision identifiers, used by Alembic.
revision = 'd0e4cbfaa5c'
down_revision = '1d9b82dfde72'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.execute('COMMIT')
    op.execute("ALTER TYPE dataset_statuses ADD value 'New';")


def downgrade():
    pass
