"""add_gradebook_tables

Revision ID: ea7443e905cb
Revises: 007_add_indexes
Create Date: 2026-01-20 14:02:27.336698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea7443e905cb'
down_revision = '007_add_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create gradebook_entries table
    op.create_table(
        'gradebook_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('term', sa.Enum('FIRST_TERM', 'SECOND_TERM', 'THIRD_TERM', 'MID_TERM', 'FINAL', 'SEMESTER_1', 'SEMESTER_2', 'ANNUAL', name='termtype'), nullable=False),
        sa.Column('quiz_weight', sa.Float(), nullable=False, server_default='0.30'),
        sa.Column('assignment_weight', sa.Float(), nullable=False, server_default='0.40'),
        sa.Column('exam_weight', sa.Float(), nullable=False, server_default='0.30'),
        sa.Column('quiz_total_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('quiz_obtained_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('quiz_weighted_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('assignment_total_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('assignment_obtained_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('assignment_weighted_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('exam_total_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('exam_obtained_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('exam_weighted_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('obtained_marks', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('letter_grade', sa.String(length=5), nullable=True),
        sa.Column('grade_point', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'class_id', 'subject_id', 'academic_year', 'term', name='uq_gradebook_entry')
    )
    op.create_index(op.f('ix_gradebook_entries_id'), 'gradebook_entries', ['id'], unique=False)
    op.create_index(op.f('ix_gradebook_entries_institute_id'), 'gradebook_entries', ['institute_id'], unique=False)
    op.create_index(op.f('ix_gradebook_entries_student_id'), 'gradebook_entries', ['student_id'], unique=False)
    op.create_index(op.f('ix_gradebook_entries_class_id'), 'gradebook_entries', ['class_id'], unique=False)
    op.create_index(op.f('ix_gradebook_entries_subject_id'), 'gradebook_entries', ['subject_id'], unique=False)
    
    # Create gradebook_history table
    op.create_table(
        'gradebook_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gradebook_entry_id', sa.Integer(), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['gradebook_entry_id'], ['gradebook_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gradebook_history_id'), 'gradebook_history', ['id'], unique=False)
    op.create_index(op.f('ix_gradebook_history_gradebook_entry_id'), 'gradebook_history', ['gradebook_entry_id'], unique=False)
    
    # Create grade_distributions table
    op.create_table(
        'grade_distributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('term', sa.Enum('FIRST_TERM', 'SECOND_TERM', 'THIRD_TERM', 'MID_TERM', 'FINAL', 'SEMESTER_1', 'SEMESTER_2', 'ANNUAL', name='termtype'), nullable=False),
        sa.Column('total_students', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('a_plus_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('a_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('b_plus_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('b_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('c_plus_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('c_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('d_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('f_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('highest_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('lowest_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'subject_id', 'academic_year', 'term', name='uq_grade_distribution')
    )
    op.create_index(op.f('ix_grade_distributions_id'), 'grade_distributions', ['id'], unique=False)
    op.create_index(op.f('ix_grade_distributions_institute_id'), 'grade_distributions', ['institute_id'], unique=False)
    op.create_index(op.f('ix_grade_distributions_class_id'), 'grade_distributions', ['class_id'], unique=False)
    op.create_index(op.f('ix_grade_distributions_subject_id'), 'grade_distributions', ['subject_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_grade_distributions_subject_id'), table_name='grade_distributions')
    op.drop_index(op.f('ix_grade_distributions_class_id'), table_name='grade_distributions')
    op.drop_index(op.f('ix_grade_distributions_institute_id'), table_name='grade_distributions')
    op.drop_index(op.f('ix_grade_distributions_id'), table_name='grade_distributions')
    op.drop_table('grade_distributions')
    op.drop_index(op.f('ix_gradebook_history_gradebook_entry_id'), table_name='gradebook_history')
    op.drop_index(op.f('ix_gradebook_history_id'), table_name='gradebook_history')
    op.drop_table('gradebook_history')
    op.drop_index(op.f('ix_gradebook_entries_subject_id'), table_name='gradebook_entries')
    op.drop_index(op.f('ix_gradebook_entries_class_id'), table_name='gradebook_entries')
    op.drop_index(op.f('ix_gradebook_entries_student_id'), table_name='gradebook_entries')
    op.drop_index(op.f('ix_gradebook_entries_institute_id'), table_name='gradebook_entries')
    op.drop_index(op.f('ix_gradebook_entries_id'), table_name='gradebook_entries')
    op.drop_table('gradebook_entries')
    op.execute("DROP TYPE IF EXISTS termtype")
