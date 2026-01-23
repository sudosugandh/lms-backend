"""add_permissions_tables

Revision ID: 86f0ba40e19a
Revises: ea7443e905cb
Create Date: 2026-01-20 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86f0ba40e19a'
down_revision = 'ea7443e905cb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module', 'action', name='uq_permission_module_action')
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    op.create_index(op.f('ix_permissions_module'), 'permissions', ['module'], unique=False)
    
    # Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'permission_id', name='uq_role_permission')
    )
    op.create_index(op.f('ix_role_permissions_id'), 'role_permissions', ['id'], unique=False)
    op.create_index(op.f('ix_role_permissions_role'), 'role_permissions', ['role'], unique=False)
    op.create_index(op.f('ix_role_permissions_permission_id'), 'role_permissions', ['permission_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_role_permissions_permission_id'), table_name='role_permissions')
    op.drop_index(op.f('ix_role_permissions_role'), table_name='role_permissions')
    op.drop_index(op.f('ix_role_permissions_id'), table_name='role_permissions')
    op.drop_table('role_permissions')
    
    op.drop_index(op.f('ix_permissions_module'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_id'), table_name='permissions')
    op.drop_table('permissions')
