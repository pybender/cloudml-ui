"""adding updated_by index

Revision ID: 1bf1ced592f8
Revises: 46a8254d3b5e
Create Date: 2016-07-29 08:11:55.905028

"""

# revision identifiers, used by Alembic.
revision = '1bf1ced592f8'
down_revision = '46a8254d3b5e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_async_task_updated_by_id', 'async_task', ['updated_by_id'], unique=False)
    op.create_index('ix_classifier_grid_params_updated_by_id', 'classifier_grid_params', ['updated_by_id'], unique=False)
    op.create_index('ix_cluster_updated_by_id', 'cluster', ['updated_by_id'], unique=False)
    op.create_index('ix_data_set_updated_by_id', 'data_set', ['updated_by_id'], unique=False)
    op.create_index('ix_feature_updated_by_id', 'feature', ['updated_by_id'], unique=False)
    op.create_index('ix_feature_set_updated_by_id', 'feature_set', ['updated_by_id'], unique=False)
    op.create_index('ix_instance_updated_by_id', 'instance', ['updated_by_id'], unique=False)
    op.create_index('ix_model_updated_by_id', 'model', ['updated_by_id'], unique=False)
    op.create_index('ix_predefined_classifier_updated_by_id', 'predefined_classifier', ['updated_by_id'], unique=False)
    op.create_index('ix_predefined_data_source_updated_by_id', 'predefined_data_source', ['updated_by_id'], unique=False)
    op.create_index('ix_predefined_feature_type_updated_by_id', 'predefined_feature_type', ['updated_by_id'], unique=False)
    op.create_index('ix_predefined_scaler_updated_by_id', 'predefined_scaler', ['updated_by_id'], unique=False)
    op.create_index('ix_server_updated_by_id', 'server', ['updated_by_id'], unique=False)
    op.create_index('ix_server_model_verification_updated_by_id', 'server_model_verification', ['updated_by_id'], unique=False)
    op.create_index('ix_test_example_updated_by_id', 'test_example', ['updated_by_id'], unique=False)
    op.create_index('ix_test_result_updated_by_id', 'test_result', ['updated_by_id'], unique=False)
    op.create_index('ix_transformer_updated_by_id', 'transformer', ['updated_by_id'], unique=False)
    op.create_index('ix_xml_import_handler_updated_by_id', 'xml_import_handler', ['updated_by_id'], unique=False)


def downgrade():
    op.drop_index('ix_xml_import_handler_updated_by_id', 'xml_import_handler')
    op.drop_index('ix_transformer_updated_by_id', 'transformer')
    op.drop_index('ix_test_result_updated_by_id', 'test_result')
    op.drop_index('ix_test_example_updated_by_id', 'test_example')
    op.drop_index('ix_server_model_verification_updated_by_id', 'server_model_verification')
    op.drop_index('ix_server_updated_by_id', 'server')
    op.drop_index('ix_predefined_scaler_updated_by_id', 'predefined_scaler')
    op.drop_index('ix_predefined_feature_type_updated_by_id', 'predefined_feature_type')
    op.drop_index('ix_predefined_data_source_updated_by_id', 'predefined_data_source')
    op.drop_index('ix_predefined_classifier_updated_by_id', 'predefined_classifier')
    op.drop_index('ix_model_updated_by_id', 'model')
    op.drop_index('ix_instance_updated_by_id', 'instance')
    op.drop_index('ix_feature_set_updated_by_id', 'feature_set')
    op.drop_index('ix_feature_updated_by_id', 'feature')
    op.drop_index('ix_data_set_updated_by_id', 'data_set')
    op.drop_index('ix_cluster_updated_by_id', 'cluster')
    op.drop_index('ix_classifier_grid_params_updated_by_id', 'classifier_grid_params')
    op.drop_index('ix_async_task_updated_by_id', 'async_task')
