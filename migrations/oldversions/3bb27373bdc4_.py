"""empty message

Revision ID: 3bb27373bdc4
Revises: 1ca38012a07d
Create Date: 2014-08-22 09:09:29.797651

"""

# revision identifiers, used by Alembic.
revision = '3bb27373bdc4'
down_revision = '1ca38012a07d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.execute('update model set trainer_size=0 where trainer_size is null')
    op.alter_column('model', 'trainer_size',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               nullable=True)
    
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    ### end Alembic commands ###
    pass
