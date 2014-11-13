"""rename Xml importhandler's field join -> delimiter

Revision ID: 57277c107fcd
Revises: 3bb27373bdc4
Create Date: 2014-09-02 09:22:59.382274

"""

# revision identifiers, used by Alembic.
revision = '57277c107fcd'
down_revision = '3bb27373bdc4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        'xml_field', 'join', new_column_name='delimiter')


def downgrade():
    op.alter_column(
        'xml_field', 'delimiter', new_column_name='join')
