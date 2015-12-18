"""adding TestResult.roc_auc

Revision ID: 12bb341247df
Revises: 57277c107fcd
Create Date: 2014-09-07 09:15:06.359824

"""

# revision identifiers, used by Alembic.
revision = '12bb341247df'
down_revision = '57277c107fcd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    from api.base.models import JSONType
    op.add_column(
        'test_result', sa.Column('roc_auc', JSONType(), nullable=True))
    op.execute(
        """update test_result set roc_auc=(metrics->'roc_auc')
        WHERE NOT metrics IS NULL""")


def downgrade():
    op.drop_column('test_result', 'roc_auc')
