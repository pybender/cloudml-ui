"""remove Predict.positive_label fk

Revision ID: 7d25aa6ef60
Revises: 28e862da77e4
Create Date: 2014-11-13 09:07:22.960313

"""

# revision identifiers, used by Alembic.
revision = '7d25aa6ef60'
down_revision = '28e862da77e4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('predict_model_positive_label_id_fkey', 'predict_model')
    op.drop_table(u'predict_model_positive_label')
    op.drop_column('predict_model', u'positive_label_id')
    op.add_column('predict_model', sa.Column('positive_label_script', sa.Text(), nullable=True))
    op.add_column('predict_model', sa.Column('positive_label_value', sa.String(length=200), nullable=True))


def downgrade():
    op.create_table(u'predict_model_positive_label',
                    sa.Column(u'id', sa.INTEGER(), nullable=False),
                    sa.Column(u'value', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
                    sa.Column(u'script', sa.TEXT(), autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint(u'id', name=u'predict_model_positive_label_pkey'),
                    )
    op.add_column('predict_model',
                  sa.Column(u'positive_label_id', sa.INTEGER(),
                            sa.ForeignKey(
                                u'predict_model_positive_label.id',
                                name=u'predict_model_positive_label_id_fkey'),
                            nullable=True))

    op.drop_column('predict_model', 'positive_label_script')
    op.drop_column('predict_model', 'positive_label_value')


