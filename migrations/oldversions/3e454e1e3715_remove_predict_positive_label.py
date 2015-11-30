"""remove Predict.positive_label

Revision ID: 3e454e1e3715
Revises: 54d3f2d13dc4
Create Date: 2015-10-12 11:27:13.743001

"""

# revision identifiers, used by Alembic.
revision = '3e454e1e3715'
down_revision = '54d3f2d13dc4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('predict_model', u'positive_label_value')
    op.drop_column('predict_model', u'positive_label_script')


def downgrade():
    op.add_column('predict_model', sa.Column(u'positive_label_script', sa.TEXT(), nullable=True))
    op.add_column('predict_model', sa.Column(u'positive_label_value', sa.VARCHAR(length=200), nullable=True))
