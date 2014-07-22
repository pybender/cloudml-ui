"""adding class_label to weights

Revision ID: 194ec8738e52
Revises: 2b86c9ec2345
Create Date: 2014-07-14 14:57:48.324645

"""

# revision identifiers, used by Alembic.
revision = '194ec8738e52'
down_revision = '2b86c9ec2345'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(u'weight', sa.Column('class_label', sa.String(100), nullable=True))


def downgrade():
    op.drop_column(u'weight', 'class_label')
