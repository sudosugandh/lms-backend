"""Add CMS tables for website management

Revision ID: 006_cms
Revises: 005_milestone5
Create Date: 2024-01-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '006_cms'
down_revision = '005_milestone5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create website_settings table
    op.create_table(
        'website_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('favicon_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=20), nullable=True),
        sa.Column('secondary_color', sa.String(length=20), nullable=True),
        sa.Column('site_name', sa.String(length=255), nullable=True),
        sa.Column('site_tagline', sa.String(length=500), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('contact_address', sa.Text(), nullable=True),
        sa.Column('meta_title', sa.String(length=255), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_keywords', sa.String(length=500), nullable=True),
        sa.Column('footer_text', sa.Text(), nullable=True),
        sa.Column('social_links', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institute_id')
    )
    op.create_index(op.f('ix_website_settings_id'), 'website_settings', ['id'], unique=False)
    op.create_index(op.f('ix_website_settings_institute_id'), 'website_settings', ['institute_id'], unique=True)
    
    # Create navigation_items table
    op.create_table(
        'navigation_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=255), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_navigation_items_id'), 'navigation_items', ['id'], unique=False)
    op.create_index(op.f('ix_navigation_items_institute_id'), 'navigation_items', ['institute_id'], unique=False)
    
    # Create page_contents table
    op.create_table(
        'page_contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('page_slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('meta_title', sa.String(length=255), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institute_id', 'page_slug', name='uq_institute_page')
    )
    op.create_index(op.f('ix_page_contents_id'), 'page_contents', ['id'], unique=False)
    op.create_index(op.f('ix_page_contents_institute_id'), 'page_contents', ['institute_id'], unique=False)
    op.create_index(op.f('ix_page_contents_page_slug'), 'page_contents', ['page_slug'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_page_contents_page_slug'), table_name='page_contents')
    op.drop_index(op.f('ix_page_contents_institute_id'), table_name='page_contents')
    op.drop_index(op.f('ix_page_contents_id'), table_name='page_contents')
    op.drop_table('page_contents')
    
    op.drop_index(op.f('ix_navigation_items_institute_id'), table_name='navigation_items')
    op.drop_index(op.f('ix_navigation_items_id'), table_name='navigation_items')
    op.drop_table('navigation_items')
    
    op.drop_index(op.f('ix_website_settings_institute_id'), table_name='website_settings')
    op.drop_index(op.f('ix_website_settings_id'), table_name='website_settings')
    op.drop_table('website_settings')
