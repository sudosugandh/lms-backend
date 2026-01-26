"""add_cms_landing_page_fields

Revision ID: add_cms_landing
Revises: b1d0ece0ef2c
Create Date: 2026-01-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_cms_landing'
down_revision = 'b1d0ece0ef2c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to website_settings table for landing page management
    op.add_column('website_settings', sa.Column('banner_images', sa.JSON(), nullable=True))
    op.add_column('website_settings', sa.Column('header_background', sa.String(length=20), nullable=True))
    op.add_column('website_settings', sa.Column('custom_css', sa.Text(), nullable=True))
    op.add_column('website_settings', sa.Column('custom_js', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove columns from website_settings table
    op.drop_column('website_settings', 'custom_js')
    op.drop_column('website_settings', 'custom_css')
    op.drop_column('website_settings', 'header_background')
    op.drop_column('website_settings', 'banner_images')
