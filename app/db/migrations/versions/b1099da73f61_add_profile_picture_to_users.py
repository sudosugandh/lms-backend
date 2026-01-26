"""add_profile_picture_to_users

Revision ID: b1099da73f61
Revises: 3b32011e9319
Create Date: 2026-01-26 23:05:57.421793

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1099da73f61'
down_revision = '3b32011e9319'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column already exists before adding
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'profile_picture' not in columns:
        op.add_column('users', sa.Column('profile_picture', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Check if column exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'profile_picture' in columns:
        op.drop_column('users', 'profile_picture')
