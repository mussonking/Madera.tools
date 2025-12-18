"""Initial MADERA MCP schema

Revision ID: initial_schema
Revises:
Create Date: 2025-01-16 00:00:00.000000

Creates all tables for MADERA MCP server:
- tool_classes: Categories for tools (hypothecaire, all_around, avocat, comptable)
- tool_templates: Learned patterns (logos, zones, thresholds)
- tool_executions: Metrics and analytics for every tool call
- training_queue: Low-confidence results for async learning
- system_settings: Configuration key-value store
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tool_classes table
    op.create_table(
        'tool_classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tool_classes_name'), 'tool_classes', ['name'], unique=False)

    # Create tool_templates table
    op.create_table(
        'tool_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('document_type', sa.String(length=100), nullable=True),
        sa.Column('logo_name', sa.String(length=100), nullable=True),
        sa.Column('logo_image', sa.LargeBinary(), nullable=True),
        sa.Column('zones', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('thresholds', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('precision_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_templates_tool_name'), 'tool_templates', ['tool_name'], unique=False)

    # Create tool_executions table
    op.create_table(
        'tool_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('outputs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('trained', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_executions_tool_name'), 'tool_executions', ['tool_name'], unique=False)
    op.create_index(op.f('ix_tool_executions_created_at'), 'tool_executions', ['created_at'], unique=False)

    # Create training_queue table
    op.create_table(
        'training_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=True),
        sa.Column('pdf_url', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['tool_executions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_training_queue_tool_name'), 'training_queue', ['tool_name'], unique=False)
    op.create_index(op.f('ix_training_queue_processed'), 'training_queue', ['processed'], unique=False)

    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=False)

    # Insert default tool classes
    op.execute("""
        INSERT INTO tool_classes (name, display_name, description, is_active, created_at) VALUES
        ('all_around', 'All Around', 'General purpose tools for any document type', true, NOW()),
        ('hypothecaire', 'Hypothécaire', 'Mortgage-specific tools for LeClasseur', true, NOW()),
        ('avocat', 'Avocat', 'Legal document tools', true, NOW()),
        ('comptable', 'Comptable', 'Accounting document tools', true, NOW())
    """)

    # Insert default system settings
    op.execute("""
        INSERT INTO system_settings (key, value, description, created_at, updated_at) VALUES
        ('blank_page_variance_threshold', '100.0', 'Pixel variance threshold for blank page detection', NOW(), NOW()),
        ('blank_page_density_threshold', '0.02', 'Text density threshold for blank page detection', NOW(), NOW()),
        ('default_pdf_dpi', '150', 'Default DPI for PDF to image conversion', NOW(), NOW()),
        ('max_file_size_mb', '50', 'Maximum file size in MB for processing', NOW(), NOW()),
        ('temp_file_cleanup_hours', '24', 'Hours before cleaning up temp files', NOW(), NOW())
    """)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('system_settings')
    op.drop_table('training_queue')
    op.drop_table('tool_executions')
    op.drop_table('tool_templates')
    op.drop_table('tool_classes')
