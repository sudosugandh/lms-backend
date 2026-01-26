"""add_smtp_email_configuration

Revision ID: 3b32011e9319
Revises: add_cms_landing
Create Date: 2026-01-26 21:54:48.658703

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3b32011e9319'
down_revision = 'add_cms_landing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add SMTP email configuration columns to website_settings table
    op.add_column('website_settings', sa.Column('smtp_host', sa.String(length=255), nullable=True))
    op.add_column('website_settings', sa.Column('smtp_port', sa.Integer(), nullable=True, server_default='587'))
    op.add_column('website_settings', sa.Column('smtp_username', sa.String(length=255), nullable=True))
    op.add_column('website_settings', sa.Column('smtp_password', sa.Text(), nullable=True))
    op.add_column('website_settings', sa.Column('smtp_use_tls', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('website_settings', sa.Column('smtp_from_email', sa.String(length=255), nullable=True))
    op.add_column('website_settings', sa.Column('smtp_from_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove SMTP columns from website_settings table
    op.drop_column('website_settings', 'smtp_from_name')
    op.drop_column('website_settings', 'smtp_from_email')
    op.drop_column('website_settings', 'smtp_use_tls')
    op.drop_column('website_settings', 'smtp_password')
    op.drop_column('website_settings', 'smtp_username')
    op.drop_column('website_settings', 'smtp_port')
    op.drop_column('website_settings', 'smtp_host')
