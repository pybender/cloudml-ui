"""predict models positive label

Revision ID: 1c8310262247
Revises: 194ec8738e52
Create Date: 2014-07-13 18:19:17.038931

"""

# revision identifiers, used by Alembic.
revision = '1c8310262247'
down_revision = '194ec8738e52'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('predict_model_positive_label_id_fkey', 'predict_model')
    op.drop_table(u'predict_model_positive_label')
    op.add_column('predict_model', sa.Column('positive_label_script', sa.Text(), nullable=True))
    op.add_column('predict_model', sa.Column('positive_label_value', sa.String(length=200), nullable=True))
    op.drop_column('predict_model', u'positive_label_id')

def downgrade():
    op.add_column('predict_model', sa.Column(u'positive_label_id', sa.INTEGER(), nullable=True))
    op.drop_column('predict_model', 'positive_label_value')
    op.drop_column('predict_model', 'positive_label_script')
    op.create_table(u'predict_model_positive_label',
    sa.Column(u'id', sa.INTEGER(), server_default="nextval('predict_model_positive_label_id_seq'::regclass)", nullable=False),
    sa.Column(u'value', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column(u'script', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint(u'id', name=u'predict_model_positive_label_pkey')
    )
