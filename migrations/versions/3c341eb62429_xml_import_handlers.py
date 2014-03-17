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
from sqlalchemy.dialects import postgresql


input_types = sa.Enum(
    'boolean', 'integer', 'float', 'date', 'string', name='xml_input_types')
datasource_type = sa.Enum(
    'http', 'db', 'pig', 'csv', name='xml_datasource_types')
field_type = sa.Enum(
    'boolean', 'integer', 'float', 'string', name='xml_field_types')
field_transform_type = sa.Enum(
    'json', 'csv', name='xml_transform_types')


def upgrade():
    op.create_table(
        'xml_query',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target', sa.String(length=200), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'xml_import_handler',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_on', sa.DateTime(),
                  server_default='now()', nullable=True),
        sa.Column('updated_on', sa.DateTime(),
                  server_default='now()', nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column(
            'import_params', postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'],
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'xml_script',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('import_handler_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['import_handler_id'],
                                ['xml_import_handler.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'xml_input_parameter',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', input_types, nullable=True),
        sa.Column('regex', sa.String(length=200), nullable=True),
        sa.Column('format', sa.String(length=200), nullable=True),
        sa.Column('import_handler_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['import_handler_id'],
                                ['xml_import_handler.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    from api.base.models import JSONType
    op.create_table(
        'xml_data_source',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', datasource_type, nullable=True),
        sa.Column('params', JSONType(), nullable=True),
        sa.Column('import_handler_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['import_handler_id'],
                                ['xml_import_handler.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'xml_entity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('datasource_name', sa.String(length=200), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('transformed_field_id', sa.Integer(), nullable=True),
        sa.Column('datasource_id', sa.Integer(), nullable=True),
        sa.Column('query_id', sa.Integer(), nullable=True),
        sa.Column('import_handler_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['datasource_id'],
                                ['xml_data_source.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['transformed_field_id'], ['xml_field.id'],
            name='fk_transformed_field', ondelete='SET NULL', use_alter=True),
        sa.ForeignKeyConstraint(['entity_id'],
                                ['xml_entity.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['import_handler_id'],
                                ['xml_import_handler.id'], ),
        sa.ForeignKeyConstraint(['query_id'],
                                ['xml_query.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'xml_field',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', field_type, nullable=True),
        sa.Column('column', sa.String(length=200), nullable=True),
        sa.Column('jsonpath', sa.String(length=200), nullable=True),
        sa.Column('join', sa.String(length=200), nullable=True),
        sa.Column('regex', sa.String(length=200), nullable=True),
        sa.Column('split', sa.String(length=200), nullable=True),
        sa.Column('dateFormat', sa.String(length=200), nullable=True),
        sa.Column('template', sa.String(length=200), nullable=True),
        sa.Column('transform', field_transform_type, nullable=True),
        sa.Column('headers', sa.String(length=200), nullable=True),
        sa.Column('script', sa.Text(), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['xml_entity.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint(None, 'xml_import_handler', ['name'])


def downgrade():
    op.drop_table('xml_field')
    op.drop_table('xml_entity')
    op.drop_table('xml_data_source')
    op.drop_table('xml_input_parameter')
    op.drop_table('xml_script')
    op.drop_table('xml_import_handler')
    op.drop_table('xml_query')
    delete_enum_types()


def delete_enum_types():
    input_types.drop(op.get_bind(), checkfirst=False)
    field_type.drop(op.get_bind(), checkfirst=False)
    field_transform_type.drop(op.get_bind(), checkfirst=False)
    datasource_type.drop(op.get_bind(), checkfirst=False)
