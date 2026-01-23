"""Milestone-2: Add classes, subjects, enrollments, attendance

Revision ID: 002_milestone2
Revises: 001_initial
Create Date: 2024-01-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002_milestone2'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update UserRole enum to include TEACHER and STUDENT
    op.execute("ALTER TABLE users MODIFY COLUMN `role` ENUM('SUPER_ADMIN', 'ADMIN', 'TEACHER', 'STUDENT') NOT NULL")
    
    # Create classes table
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_classes_id'), 'classes', ['id'], unique=False)
    op.create_index(op.f('ix_classes_institute_id'), 'classes', ['institute_id'], unique=False)
    
    # Create subjects table
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subjects_id'), 'subjects', ['id'], unique=False)
    op.create_index(op.f('ix_subjects_institute_id'), 'subjects', ['institute_id'], unique=False)
    
    # Create class_subjects table
    op.create_table(
        'class_subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'subject_id', name='uq_class_subject')
    )
    op.create_index(op.f('ix_class_subjects_id'), 'class_subjects', ['id'], unique=False)
    op.create_index(op.f('ix_class_subjects_class_id'), 'class_subjects', ['class_id'], unique=False)
    op.create_index(op.f('ix_class_subjects_subject_id'), 'class_subjects', ['subject_id'], unique=False)
    op.create_index(op.f('ix_class_subjects_teacher_id'), 'class_subjects', ['teacher_id'], unique=False)
    
    # Create enrollments table
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'class_id', name='uq_student_class')
    )
    op.create_index(op.f('ix_enrollments_id'), 'enrollments', ['id'], unique=False)
    op.create_index(op.f('ix_enrollments_student_id'), 'enrollments', ['student_id'], unique=False)
    op.create_index(op.f('ix_enrollments_class_id'), 'enrollments', ['class_id'], unique=False)
    
    # Create attendance table
    op.create_table(
        'attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('marked_by', sa.Integer(), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['marked_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'class_id', 'subject_id', 'attendance_date', name='uq_attendance')
    )
    op.create_index(op.f('ix_attendance_id'), 'attendance', ['id'], unique=False)
    op.create_index(op.f('ix_attendance_student_id'), 'attendance', ['student_id'], unique=False)
    op.create_index(op.f('ix_attendance_class_id'), 'attendance', ['class_id'], unique=False)
    op.create_index(op.f('ix_attendance_subject_id'), 'attendance', ['subject_id'], unique=False)
    op.create_index(op.f('ix_attendance_attendance_date'), 'attendance', ['attendance_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_attendance_attendance_date'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_subject_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_class_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_student_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_id'), table_name='attendance')
    op.drop_table('attendance')
    
    op.drop_index(op.f('ix_enrollments_class_id'), table_name='enrollments')
    op.drop_index(op.f('ix_enrollments_student_id'), table_name='enrollments')
    op.drop_index(op.f('ix_enrollments_id'), table_name='enrollments')
    op.drop_table('enrollments')
    
    op.drop_index(op.f('ix_class_subjects_teacher_id'), table_name='class_subjects')
    op.drop_index(op.f('ix_class_subjects_subject_id'), table_name='class_subjects')
    op.drop_index(op.f('ix_class_subjects_class_id'), table_name='class_subjects')
    op.drop_index(op.f('ix_class_subjects_id'), table_name='class_subjects')
    op.drop_table('class_subjects')
    
    op.drop_index(op.f('ix_subjects_institute_id'), table_name='subjects')
    op.drop_index(op.f('ix_subjects_id'), table_name='subjects')
    op.drop_table('subjects')
    
    op.drop_index(op.f('ix_classes_institute_id'), table_name='classes')
    op.drop_index(op.f('ix_classes_id'), table_name='classes')
    op.drop_table('classes')
    
    # Revert UserRole enum
    op.execute("ALTER TABLE users MODIFY COLUMN `role` ENUM('SUPER_ADMIN', 'ADMIN') NOT NULL")
