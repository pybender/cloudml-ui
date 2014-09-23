"""remove predefined transformers

Revision ID: 26a159467f7a
Revises: 403c519d5ffc
Create Date: 2014-09-23 08:40:12.135252

"""

# revision identifiers, used by Alembic.
revision = '26a159467f7a'
down_revision = '403c519d5ffc'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_table(u'predefined_transformer')


def downgrade():
    op.create_table(u'predefined_transformer',
        sa.Column(u'id', sa.INTEGER(), server_default="nextval('predefined_transformer_id_seq'::regclass)", nullable=False),
        sa.Column(u'created_on', postgresql.TIMESTAMP(), server_default='now()', autoincrement=False, nullable=True),
        sa.Column(u'updated_on', postgresql.TIMESTAMP(), server_default='now()', autoincrement=False, nullable=True),
        sa.Column(u'name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
        sa.Column(u'type', postgresql.ENUM(u'Count', u'Tfidf', u'Lda', u'Dictionary', u'Lsi', name=u'transformer_types'), autoincrement=False, nullable=False),
        sa.Column(u'updated_by_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(u'created_by_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(u'params', sa.PostgresJSON(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], [u'user.id'], name=u'predefined_transformer_created_by_id_fkey'),
        sa.ForeignKeyConstraint(['updated_by_id'], [u'user.id'], name=u'predefined_transformer_updated_by_id_fkey'),
        sa.PrimaryKeyConstraint(u'id', name=u'predefined_transformer_pkey')
    )
