"""Milestone-4: Add leave management, timetables, and notifications

Revision ID: 004_milestone4
Revises: 003_milestone3
Create Date: 2024-01-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '004_milestone4'
down_revision = '003_milestone3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create leave_types table
    op.create_table(
        'leave_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_days_per_year', sa.Integer(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leave_types_id'), 'leave_types', ['id'], unique=False)
    op.create_index(op.f('ix_leave_types_institute_id'), 'leave_types', ['institute_id'], unique=False)
    
    # Create leave_requests table
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('leave_type_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('number_of_days', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leave_requests_id'), 'leave_requests', ['id'], unique=False)
    op.create_index(op.f('ix_leave_requests_institute_id'), 'leave_requests', ['institute_id'], unique=False)
    op.create_index(op.f('ix_leave_requests_user_id'), 'leave_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_leave_requests_leave_type_id'), 'leave_requests', ['leave_type_id'], unique=False)
    op.create_index(op.f('ix_leave_requests_start_date'), 'leave_requests', ['start_date'], unique=False)
    op.create_index(op.f('ix_leave_requests_end_date'), 'leave_requests', ['end_date'], unique=False)
    
    # Create timetables table
    op.create_table(
        'timetables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('academic_year', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timetables_id'), 'timetables', ['id'], unique=False)
    op.create_index(op.f('ix_timetables_institute_id'), 'timetables', ['institute_id'], unique=False)
    op.create_index(op.f('ix_timetables_class_id'), 'timetables', ['class_id'], unique=False)
    
    # Create timetable_slots table
    op.create_table(
        'timetable_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timetable_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['timetable_id'], ['timetables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('timetable_id', 'day_of_week', 'period_number', name='uq_timetable_day_period')
    )
    op.create_index(op.f('ix_timetable_slots_id'), 'timetable_slots', ['id'], unique=False)
    op.create_index(op.f('ix_timetable_slots_timetable_id'), 'timetable_slots', ['timetable_id'], unique=False)
    
    # Create timetable_assignments table
    op.create_table(
        'timetable_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('room', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['slot_id'], ['timetable_slots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slot_id', 'subject_id', name='uq_slot_subject')
    )
    op.create_index(op.f('ix_timetable_assignments_id'), 'timetable_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_timetable_assignments_slot_id'), 'timetable_assignments', ['slot_id'], unique=False)
    op.create_index(op.f('ix_timetable_assignments_subject_id'), 'timetable_assignments', ['subject_id'], unique=False)
    op.create_index(op.f('ix_timetable_assignments_teacher_id'), 'timetable_assignments', ['teacher_id'], unique=False)
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('target_role', sa.String(length=20), nullable=True),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('target_class_id', sa.Integer(), nullable=True),
        sa.Column('notification_metadata', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_institute_id'), 'notifications', ['institute_id'], unique=False)
    op.create_index(op.f('ix_notifications_target_user_id'), 'notifications', ['target_user_id'], unique=False)
    op.create_index(op.f('ix_notifications_target_class_id'), 'notifications', ['target_class_id'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    
    # Create notification_read_status table
    op.create_table(
        'notification_read_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notification_id', 'user_id', name='uq_notification_user')
    )
    op.create_index(op.f('ix_notification_read_status_id'), 'notification_read_status', ['id'], unique=False)
    op.create_index(op.f('ix_notification_read_status_notification_id'), 'notification_read_status', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_read_status_user_id'), 'notification_read_status', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_read_status_user_id'), table_name='notification_read_status')
    op.drop_index(op.f('ix_notification_read_status_notification_id'), table_name='notification_read_status')
    op.drop_index(op.f('ix_notification_read_status_id'), table_name='notification_read_status')
    op.drop_table('notification_read_status')
    
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_target_class_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_target_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_institute_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index(op.f('ix_timetable_assignments_teacher_id'), table_name='timetable_assignments')
    op.drop_index(op.f('ix_timetable_assignments_subject_id'), table_name='timetable_assignments')
    op.drop_index(op.f('ix_timetable_assignments_slot_id'), table_name='timetable_assignments')
    op.drop_index(op.f('ix_timetable_assignments_id'), table_name='timetable_assignments')
    op.drop_table('timetable_assignments')
    
    op.drop_index(op.f('ix_timetable_slots_timetable_id'), table_name='timetable_slots')
    op.drop_index(op.f('ix_timetable_slots_id'), table_name='timetable_slots')
    op.drop_table('timetable_slots')
    
    op.drop_index(op.f('ix_timetables_class_id'), table_name='timetables')
    op.drop_index(op.f('ix_timetables_institute_id'), table_name='timetables')
    op.drop_index(op.f('ix_timetables_id'), table_name='timetables')
    op.drop_table('timetables')
    
    op.drop_index(op.f('ix_leave_requests_end_date'), table_name='leave_requests')
    op.drop_index(op.f('ix_leave_requests_start_date'), table_name='leave_requests')
    op.drop_index(op.f('ix_leave_requests_leave_type_id'), table_name='leave_requests')
    op.drop_index(op.f('ix_leave_requests_user_id'), table_name='leave_requests')
    op.drop_index(op.f('ix_leave_requests_institute_id'), table_name='leave_requests')
    op.drop_index(op.f('ix_leave_requests_id'), table_name='leave_requests')
    op.drop_table('leave_requests')
    
    op.drop_index(op.f('ix_leave_types_institute_id'), table_name='leave_types')
    op.drop_index(op.f('ix_leave_types_id'), table_name='leave_types')
    op.drop_table('leave_types')
