"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""
    
    # Create custom types
    op.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE contentstatus AS ENUM ('draft', 'review', 'approved', 'published', 'archived')")
    op.execute("CREATE TYPE qualitystatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE contenttype AS ENUM ('video', 'interactive', 'quiz', 'mixed')")
    op.execute("CREATE TYPE interactiontype AS ENUM ('view', 'complete', 'share', 'feedback', 'quiz_attempt')")
    op.execute("CREATE TYPE exportformat AS ENUM ('mp4', 'pdf', 'html', 'scorm', 'markdown')")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean(), default=False, nullable=False),
        sa.Column('email_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('profile_data', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('preferences', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action')
    )
    
    # Create user_roles junction table
    op.create_table('user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    # Create role_permissions junction table
    op.create_table('role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Create content_generations table
    op.create_table('content_generations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_file_path', sa.String(500), nullable=False),
        sa.Column('source_file_name', sa.String(255), nullable=False),
        sa.Column('source_file_size', sa.Integer(), nullable=True),
        sa.Column('content_type', postgresql.ENUM('video', 'interactive', 'quiz', 'mixed', name='contenttype'), nullable=False),
        sa.Column('target_audience', sa.String(255), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', name='taskstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), default=0, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('settings', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('total_tokens_used', sa.Integer(), default=0, nullable=False),
        sa.Column('user_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_content_generations_user_id', 'content_generations', ['user_id'])
    op.create_index('ix_content_generations_status', 'content_generations', ['status'])
    op.create_index('ix_content_generations_created_at', 'content_generations', ['created_at'])


def downgrade() -> None:
    """Drop all tables and types."""
    op.drop_index('ix_content_generations_created_at')
    op.drop_index('ix_content_generations_status')
    op.drop_index('ix_content_generations_user_id')
    op.drop_index('ix_users_email')
    
    op.drop_table('content_generations')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    
    op.execute('DROP TYPE IF EXISTS exportformat')
    op.execute('DROP TYPE IF EXISTS interactiontype')
    op.execute('DROP TYPE IF EXISTS contenttype')
    op.execute('DROP TYPE IF EXISTS qualitystatus')
    op.execute('DROP TYPE IF EXISTS contentstatus')
    op.execute('DROP TYPE IF EXISTS taskstatus')
