"""Add database indexes and constraints for performance

Revision ID: 007_add_indexes
Revises: 006_cms
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '007_add_indexes'
down_revision = '006_cms'
branch_labels = None
depends_on = None


def table_exists(conn, table_name):
    """Check if a table exists."""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def index_exists(conn, table_name, index_name):
    """Check if an index exists on a table."""
    if not table_exists(conn, table_name):
        return False
    inspector = inspect(conn)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade():
    conn = op.get_bind()
    
    # Add indexes for frequently queried columns
    # Users table - add index on institute_id + role for faster lookups
    if not index_exists(conn, 'users', 'ix_users_institute_role'):
        op.create_index('ix_users_institute_role', 'users', ['institute_id', 'role'], unique=False)
    
    # Attendance table - add composite index for date range queries
    if not index_exists(conn, 'attendance', 'ix_attendance_date_class'):
        op.create_index('ix_attendance_date_class', 'attendance', ['attendance_date', 'class_id'], unique=False)
    if not index_exists(conn, 'attendance', 'ix_attendance_student_date'):
        op.create_index('ix_attendance_student_date', 'attendance', ['student_id', 'attendance_date'], unique=False)
    
    # Results table - add indexes for filtering
    if not index_exists(conn, 'results', 'ix_results_student_type'):
        op.create_index('ix_results_student_type', 'results', ['student_id', 'result_type'], unique=False)
    if not index_exists(conn, 'results', 'ix_results_class_subject'):
        op.create_index('ix_results_class_subject', 'results', ['class_id', 'subject_id'], unique=False)
    
    # Quizzes table - add index for published quizzes lookup
    if not index_exists(conn, 'quizzes', 'ix_quizzes_class_status'):
        op.create_index('ix_quizzes_class_status', 'quizzes', ['class_id', 'status'], unique=False)
    if not index_exists(conn, 'quizzes', 'ix_quizzes_institute_active'):
        op.create_index('ix_quizzes_institute_active', 'quizzes', ['institute_id', 'is_active'], unique=False)
    
    # Assignments table - add index for deadline queries
    if not index_exists(conn, 'assignments', 'ix_assignments_class_deadline'):
        op.create_index('ix_assignments_class_deadline', 'assignments', ['class_id', 'deadline'], unique=False)
    if not index_exists(conn, 'assignments', 'ix_assignments_institute_active'):
        op.create_index('ix_assignments_institute_active', 'assignments', ['institute_id', 'is_active'], unique=False)
    
    # Notifications table - add index for user notifications
    if not index_exists(conn, 'notifications', 'ix_notifications_institute_created'):
        op.create_index('ix_notifications_institute_created', 'notifications', ['institute_id', 'created_at'], unique=False)
    if not index_exists(conn, 'notifications', 'ix_notifications_target_user'):
        op.create_index('ix_notifications_target_user', 'notifications', ['target_user_id', 'is_active'], unique=False)
    
    # Notification read status - add index for unread count queries
    if not index_exists(conn, 'notification_read_status', 'ix_notification_read_user_read'):
        op.create_index('ix_notification_read_user_read', 'notification_read_status', ['user_id', 'is_read'], unique=False)
    
    # Leave requests - add index for status filtering
    if not index_exists(conn, 'leave_requests', 'ix_leave_requests_user_status'):
        op.create_index('ix_leave_requests_user_status', 'leave_requests', ['user_id', 'status'], unique=False)
    if not index_exists(conn, 'leave_requests', 'ix_leave_requests_institute_status'):
        op.create_index('ix_leave_requests_institute_status', 'leave_requests', ['institute_id', 'status'], unique=False)
    
    # Fee invoices - add index for status and student queries
    if not index_exists(conn, 'fee_invoices', 'ix_fee_invoices_student_status'):
        op.create_index('ix_fee_invoices_student_status', 'fee_invoices', ['student_id', 'status'], unique=False)
    if not index_exists(conn, 'fee_invoices', 'ix_fee_invoices_institute_status'):
        op.create_index('ix_fee_invoices_institute_status', 'fee_invoices', ['institute_id', 'status'], unique=False)
    
    # Certificate issuances - add index for student lookups
    if not index_exists(conn, 'certificate_issuance', 'ix_certificate_issuance_student'):
        op.create_index('ix_certificate_issuance_student', 'certificate_issuance', ['student_id', 'is_active'], unique=False)
    
    # Timetable assignments - add index for teacher lookups
    if not index_exists(conn, 'timetable_assignments', 'ix_timetable_assignments_teacher'):
        op.create_index('ix_timetable_assignments_teacher', 'timetable_assignments', ['teacher_id', 'is_active'], unique=False)
    
    # Audit logs - add index for user action queries
    if not index_exists(conn, 'audit_logs', 'ix_audit_logs_user_created'):
        op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)
    if not index_exists(conn, 'audit_logs', 'ix_audit_logs_action'):
        op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)


def downgrade():
    # Remove indexes (only if they exist)
    conn = op.get_bind()
    
    indexes_to_drop = [
        ('users', 'ix_users_institute_role'),
        ('attendance', 'ix_attendance_date_class'),
        ('attendance', 'ix_attendance_student_date'),
        ('results', 'ix_results_student_type'),
        ('results', 'ix_results_class_subject'),
        ('quizzes', 'ix_quizzes_class_status'),
        ('quizzes', 'ix_quizzes_institute_active'),
        ('assignments', 'ix_assignments_class_deadline'),
        ('assignments', 'ix_assignments_institute_active'),
        ('notifications', 'ix_notifications_institute_created'),
        ('notifications', 'ix_notifications_target_user'),
        ('notification_read_status', 'ix_notification_read_user_read'),
        ('leave_requests', 'ix_leave_requests_user_status'),
        ('leave_requests', 'ix_leave_requests_institute_status'),
        ('fee_invoices', 'ix_fee_invoices_student_status'),
        ('fee_invoices', 'ix_fee_invoices_institute_status'),
        ('certificate_issuance', 'ix_certificate_issuance_student'),
        ('timetable_assignments', 'ix_timetable_assignments_teacher'),
        ('audit_logs', 'ix_audit_logs_user_created'),
        ('audit_logs', 'ix_audit_logs_action'),
    ]
    
    for table_name, index_name in indexes_to_drop:
        if index_exists(conn, table_name, index_name):
            op.drop_index(index_name, table_name=table_name)
