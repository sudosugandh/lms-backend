"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create institutes table
    op.create_table(
        'institutes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_institutes_id'), 'institutes', ['id'], unique=False)
    op.create_index(op.f('ix_institutes_name'), 'institutes', ['name'], unique=False)
    op.create_index(op.f('ix_institutes_code'), 'institutes', ['code'], unique=True)
    
    # Create domains table
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('host_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_domains_id'), 'domains', ['id'], unique=False)
    op.create_index(op.f('ix_domains_institute_id'), 'domains', ['institute_id'], unique=False)
    op.create_index(op.f('ix_domains_host_name'), 'domains', ['host_name'], unique=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_institute_id'), 'users', ['institute_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_institute_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_domains_host_name'), table_name='domains')
    op.drop_index(op.f('ix_domains_institute_id'), table_name='domains')
    op.drop_index(op.f('ix_domains_id'), table_name='domains')
    op.drop_table('domains')
    
    op.drop_index(op.f('ix_institutes_code'), table_name='institutes')
    op.drop_index(op.f('ix_institutes_name'), table_name='institutes')
    op.drop_index(op.f('ix_institutes_id'), table_name='institutes')
    op.drop_table('institutes')
    
    op.execute('DROP TYPE IF EXISTS userrole')
