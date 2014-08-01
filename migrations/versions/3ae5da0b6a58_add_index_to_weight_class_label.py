"""add index to weight.class_label

Revision ID: 3ae5da0b6a58
Revises: 194ec8738e52
Create Date: 2014-08-01 19:55:10.077015

"""

# revision identifiers, used by Alembic.
revision = '3ae5da0b6a58'
down_revision = '194ec8738e52'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index(u'ix_weight_class_label', u'weight', [u'class_label'])


def downgrade():
    op.drop_index(u'ix_weight_class_label')
