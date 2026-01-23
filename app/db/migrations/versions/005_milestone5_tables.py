"""Milestone-5: Add parent portal, fee management, and certificates

Revision ID: 005_milestone5
Revises: 004_milestone4
Create Date: 2024-01-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '005_milestone5'
down_revision = '004_milestone4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update UserRole enum to include PARENT
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('SUPER_ADMIN', 'ADMIN', 'TEACHER', 'STUDENT', 'PARENT') NOT NULL")
    
    # Create parent_student_links table
    op.create_table(
        'parent_student_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_id', 'student_id', name='uq_parent_student')
    )
    op.create_index(op.f('ix_parent_student_links_id'), 'parent_student_links', ['id'], unique=False)
    op.create_index(op.f('ix_parent_student_links_parent_id'), 'parent_student_links', ['parent_id'], unique=False)
    op.create_index(op.f('ix_parent_student_links_student_id'), 'parent_student_links', ['student_id'], unique=False)
    
    # Create fee_structures table
    op.create_table(
        'fee_structures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('academic_year', sa.String(length=50), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fee_structures_id'), 'fee_structures', ['id'], unique=False)
    op.create_index(op.f('ix_fee_structures_institute_id'), 'fee_structures', ['institute_id'], unique=False)
    op.create_index(op.f('ix_fee_structures_class_id'), 'fee_structures', ['class_id'], unique=False)
    
    # Create fee_invoices table
    op.create_table(
        'fee_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('fee_structure_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), nullable=False),
        sa.Column('due_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['fee_structures.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number')
    )
    op.create_index(op.f('ix_fee_invoices_id'), 'fee_invoices', ['id'], unique=False)
    op.create_index(op.f('ix_fee_invoices_institute_id'), 'fee_invoices', ['institute_id'], unique=False)
    op.create_index(op.f('ix_fee_invoices_student_id'), 'fee_invoices', ['student_id'], unique=False)
    op.create_index(op.f('ix_fee_invoices_fee_structure_id'), 'fee_invoices', ['fee_structure_id'], unique=False)
    op.create_index(op.f('ix_fee_invoices_due_date'), 'fee_invoices', ['due_date'], unique=False)
    
    # Create fee_payments table
    op.create_table(
        'fee_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('receipt_number', sa.String(length=100), nullable=True),
        sa.Column('transaction_reference', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['fee_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fee_payments_id'), 'fee_payments', ['id'], unique=False)
    op.create_index(op.f('ix_fee_payments_invoice_id'), 'fee_payments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_fee_payments_payment_date'), 'fee_payments', ['payment_date'], unique=False)
    
    # Create certificate_templates table
    op.create_table(
        'certificate_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('certificate_type', sa.String(length=50), nullable=False),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('placeholders', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certificate_templates_id'), 'certificate_templates', ['id'], unique=False)
    op.create_index(op.f('ix_certificate_templates_institute_id'), 'certificate_templates', ['institute_id'], unique=False)
    
    # Create certificate_issuance table
    op.create_table(
        'certificate_issuance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('certificate_number', sa.String(length=100), nullable=False),
        sa.Column('certificate_content', sa.Text(), nullable=False),
        sa.Column('certificate_url', sa.String(length=500), nullable=True),
        sa.Column('issued_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('certificate_metadata', sa.Text(), nullable=True),
        sa.Column('issued_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['certificate_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('certificate_number', 'institute_id', name='uq_certificate_number')
    )
    op.create_index(op.f('ix_certificate_issuance_id'), 'certificate_issuance', ['id'], unique=False)
    op.create_index(op.f('ix_certificate_issuance_institute_id'), 'certificate_issuance', ['institute_id'], unique=False)
    op.create_index(op.f('ix_certificate_issuance_student_id'), 'certificate_issuance', ['student_id'], unique=False)
    op.create_index(op.f('ix_certificate_issuance_template_id'), 'certificate_issuance', ['template_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_certificate_issuance_template_id'), table_name='certificate_issuance')
    op.drop_index(op.f('ix_certificate_issuance_student_id'), table_name='certificate_issuance')
    op.drop_index(op.f('ix_certificate_issuance_institute_id'), table_name='certificate_issuance')
    op.drop_index(op.f('ix_certificate_issuance_id'), table_name='certificate_issuance')
    op.drop_table('certificate_issuance')
    
    op.drop_index(op.f('ix_certificate_templates_institute_id'), table_name='certificate_templates')
    op.drop_index(op.f('ix_certificate_templates_id'), table_name='certificate_templates')
    op.drop_table('certificate_templates')
    
    op.drop_index(op.f('ix_fee_payments_payment_date'), table_name='fee_payments')
    op.drop_index(op.f('ix_fee_payments_invoice_id'), table_name='fee_payments')
    op.drop_index(op.f('ix_fee_payments_id'), table_name='fee_payments')
    op.drop_table('fee_payments')
    
    op.drop_index(op.f('ix_fee_invoices_due_date'), table_name='fee_invoices')
    op.drop_index(op.f('ix_fee_invoices_fee_structure_id'), table_name='fee_invoices')
    op.drop_index(op.f('ix_fee_invoices_student_id'), table_name='fee_invoices')
    op.drop_index(op.f('ix_fee_invoices_institute_id'), table_name='fee_invoices')
    op.drop_index(op.f('ix_fee_invoices_id'), table_name='fee_invoices')
    op.drop_table('fee_invoices')
    
    op.drop_index(op.f('ix_fee_structures_class_id'), table_name='fee_structures')
    op.drop_index(op.f('ix_fee_structures_institute_id'), table_name='fee_structures')
    op.drop_index(op.f('ix_fee_structures_id'), table_name='fee_structures')
    op.drop_table('fee_structures')
    
    op.drop_index(op.f('ix_parent_student_links_student_id'), table_name='parent_student_links')
    op.drop_index(op.f('ix_parent_student_links_parent_id'), table_name='parent_student_links')
    op.drop_index(op.f('ix_parent_student_links_id'), table_name='parent_student_links')
    op.drop_table('parent_student_links')
    
    # Revert UserRole enum
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('SUPER_ADMIN', 'ADMIN', 'TEACHER', 'STUDENT') NOT NULL")
