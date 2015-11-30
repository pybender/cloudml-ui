"""adding filling weights to model.statuses

Revision ID: aeb5a592587
Revises: 190872916592
Create Date: 2014-11-02 09:36:52.051648

"""

# revision identifiers, used by Alembic.
revision = 'aeb5a592587'
down_revision = '190872916592'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.execute('COMMIT')
    op.execute("ALTER TYPE model_statuses ADD value 'Filling Weights';")


def downgrade():
    pass
