"""add_pages_and_translations_tables

Revision ID: b1d0ece0ef2c
Revises: 86f0ba40e19a
Create Date: 2026-01-20 21:08:22.300345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1d0ece0ef2c'
down_revision = '86f0ba40e19a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pages table
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('page_type', sa.Enum('CUSTOM', 'HOME', 'ABOUT', 'CONTACT', 'CAREERS', name='pagetype'), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('add_in_header_menu', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('show_menu_on_footer', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('show_after_login', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('show_only_to_logged_in_user', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('enable_tab', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('use_web_view_url', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('enable_for_blog', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('widget_color', sa.String(length=20), nullable=True),
        sa.Column('custom_page_url', sa.String(length=500), nullable=True),
        sa.Column('page_id', sa.Integer(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institute_id', 'slug', name='uq_institute_page_slug')
    )
    op.create_index(op.f('ix_pages_id'), 'pages', ['id'], unique=False)
    op.create_index(op.f('ix_pages_institute_id'), 'pages', ['institute_id'], unique=False)
    op.create_index(op.f('ix_pages_slug'), 'pages', ['slug'], unique=False)
    op.create_index(op.f('ix_pages_sequence'), 'pages', ['sequence'], unique=False)
    op.create_index(op.f('ix_pages_page_id'), 'pages', ['page_id'], unique=False)
    op.create_index(op.f('ix_pages_is_approved'), 'pages', ['is_approved'], unique=False)
    
    # Create page_translations table
    op.create_table(
        'page_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedded_code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('page_id', 'locale', name='uq_page_translation')
    )
    op.create_index(op.f('ix_page_translations_id'), 'page_translations', ['id'], unique=False)
    op.create_index(op.f('ix_page_translations_page_id'), 'page_translations', ['page_id'], unique=False)
    op.create_index(op.f('ix_page_translations_locale'), 'page_translations', ['locale'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_page_translations_locale'), table_name='page_translations')
    op.drop_index(op.f('ix_page_translations_page_id'), table_name='page_translations')
    op.drop_index(op.f('ix_page_translations_id'), table_name='page_translations')
    op.drop_table('page_translations')
    
    op.drop_index(op.f('ix_pages_is_approved'), table_name='pages')
    op.drop_index(op.f('ix_pages_page_id'), table_name='pages')
    op.drop_index(op.f('ix_pages_sequence'), table_name='pages')
    op.drop_index(op.f('ix_pages_slug'), table_name='pages')
    op.drop_index(op.f('ix_pages_institute_id'), table_name='pages')
    op.drop_index(op.f('ix_pages_id'), table_name='pages')
    op.drop_table('pages')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS pagetype")
