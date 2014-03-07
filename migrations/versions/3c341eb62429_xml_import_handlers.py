"""xml import handlers

Revision ID: 3c341eb62429
Revises: 1cb1aef8263f
Create Date: 2014-03-07 15:07:56.266983

"""

# revision identifiers, used by Alembic.
revision = '3c341eb62429'
down_revision = '1cb1aef8263f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('query',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target', sa.String(length=200), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('xml_import_handler',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default='now()', nullable=True),
    sa.Column('updated_on', sa.DateTime(), server_default='now()', nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('script',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data', sa.String(length=200), nullable=True),
    sa.Column('import_handler_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['import_handler_id'], ['xml_import_handler.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('input_parameter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', sa.Enum('boolean', 'integer', 'float', 'date', 'string', name='xml_input_types'), nullable=True),
    sa.Column('regex', sa.String(length=200), nullable=True),
    sa.Column('format', sa.String(length=200), nullable=True),
    sa.Column('import_handler_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['import_handler_id'], ['xml_import_handler.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    from api.base.models import JSONType
    op.create_table('xml_data_source',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', sa.Enum('http', 'db', 'pig', name='xml_datasource_types'), nullable=True),
    sa.Column('params', JSONType(), nullable=True),
    sa.Column('import_handler_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['import_handler_id'], ['xml_import_handler.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('entity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('datasource_id', sa.Integer(), nullable=True),
    sa.Column('query_id', sa.Integer(), nullable=True),
    sa.Column('import_handler_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['datasource_id'], ['xml_data_source.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['import_handler_id'], ['xml_import_handler.id'], ),
    sa.ForeignKeyConstraint(['query_id'], ['query.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('field',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', sa.Enum('boolean', 'integer', 'float', 'string', name='xml_field_types'), nullable=True),
    sa.Column('column', sa.String(length=200), nullable=True),
    sa.Column('jsonpath', sa.String(length=200), nullable=True),
    sa.Column('join', sa.String(length=200), nullable=True),
    sa.Column('regex', sa.String(length=200), nullable=True),
    sa.Column('split', sa.String(length=200), nullable=True),
    sa.Column('dateFormat', sa.String(length=200), nullable=True),
    sa.Column('template', sa.String(length=200), nullable=True),
    sa.Column('transform', sa.Enum('json', 'csv', name='xml_transform_types'), nullable=True),
    sa.Column('headers', sa.String(length=200), nullable=True),
    sa.Column('script_id', sa.Integer(), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['script_id'], ['script.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'data_set', sa.Column('import_handler_xml_id', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'data_set', 'import_handler_xml_id')
    op.drop_table('field')
    op.drop_table('entity')
    op.drop_table('xml_data_source')
    op.drop_table('input_parameter')
    op.drop_table('script')
    op.drop_table('xml_import_handler')
    op.drop_table('query')
    ### end Alembic commands ###
