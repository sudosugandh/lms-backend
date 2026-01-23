"""Milestone-3: Add quizzes, assignments, and results

Revision ID: 003_milestone3
Revises: 002_milestone2
Create Date: 2024-01-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_milestone3'
down_revision = '002_milestone2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('total_marks', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('allow_multiple_attempts', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quizzes_id'), 'quizzes', ['id'], unique=False)
    op.create_index(op.f('ix_quizzes_institute_id'), 'quizzes', ['institute_id'], unique=False)
    op.create_index(op.f('ix_quizzes_class_id'), 'quizzes', ['class_id'], unique=False)
    op.create_index(op.f('ix_quizzes_subject_id'), 'quizzes', ['subject_id'], unique=False)
    op.create_index(op.f('ix_quizzes_created_by'), 'quizzes', ['created_by'], unique=False)
    
    # Create quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=20), nullable=False),
        sa.Column('marks', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_questions_id'), 'quiz_questions', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_questions_quiz_id'), 'quiz_questions', ['quiz_id'], unique=False)
    
    # Create quiz_options table
    op.create_table(
        'quiz_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_options_id'), 'quiz_options', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_options_question_id'), 'quiz_options', ['question_id'], unique=False)
    
    # Create quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_taken_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('total_marks_obtained', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_attempts_id'), 'quiz_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_quiz_id'), 'quiz_attempts', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_student_id'), 'quiz_attempts', ['student_id'], unique=False)
    
    # Create quiz_attempt_answers table
    op.create_table(
        'quiz_attempt_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_option_id', sa.Integer(), nullable=True),
        sa.Column('descriptive_answer', sa.Text(), nullable=True),
        sa.Column('marks_obtained', sa.Integer(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('graded_by', sa.Integer(), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['quiz_options.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['graded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_attempt_answers_id'), 'quiz_attempt_answers', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_attempt_answers_attempt_id'), 'quiz_attempt_answers', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_quiz_attempt_answers_question_id'), 'quiz_attempt_answers', ['question_id'], unique=False)
    
    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('total_marks', sa.Integer(), nullable=False),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('allow_late_submission', sa.Boolean(), nullable=False),
        sa.Column('attachment_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_id'), 'assignments', ['id'], unique=False)
    op.create_index(op.f('ix_assignments_institute_id'), 'assignments', ['institute_id'], unique=False)
    op.create_index(op.f('ix_assignments_class_id'), 'assignments', ['class_id'], unique=False)
    op.create_index(op.f('ix_assignments_subject_id'), 'assignments', ['subject_id'], unique=False)
    op.create_index(op.f('ix_assignments_created_by'), 'assignments', ['created_by'], unique=False)
    
    # Create assignment_submissions table
    op.create_table(
        'assignment_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('submission_text', sa.Text(), nullable=True),
        sa.Column('attachment_url', sa.String(length=500), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_late', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('marks_obtained', sa.Integer(), nullable=True),
        sa.Column('graded_by', sa.Integer(), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['graded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'student_id', name='uq_assignment_student')
    )
    op.create_index(op.f('ix_assignment_submissions_id'), 'assignment_submissions', ['id'], unique=False)
    op.create_index(op.f('ix_assignment_submissions_assignment_id'), 'assignment_submissions', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_assignment_submissions_student_id'), 'assignment_submissions', ['student_id'], unique=False)
    
    # Create results table
    op.create_table(
        'results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=True),
        sa.Column('assignment_id', sa.Integer(), nullable=True),
        sa.Column('quiz_attempt_id', sa.Integer(), nullable=True),
        sa.Column('assignment_submission_id', sa.Integer(), nullable=True),
        sa.Column('result_type', sa.String(length=20), nullable=False),
        sa.Column('total_marks', sa.Integer(), nullable=False),
        sa.Column('marks_obtained', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_attempt_id'], ['quiz_attempts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assignment_submission_id'], ['assignment_submissions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'quiz_id', name='uq_student_quiz_result'),
        sa.UniqueConstraint('student_id', 'assignment_id', name='uq_student_assignment_result')
    )
    op.create_index(op.f('ix_results_id'), 'results', ['id'], unique=False)
    op.create_index(op.f('ix_results_institute_id'), 'results', ['institute_id'], unique=False)
    op.create_index(op.f('ix_results_student_id'), 'results', ['student_id'], unique=False)
    op.create_index(op.f('ix_results_class_id'), 'results', ['class_id'], unique=False)
    op.create_index(op.f('ix_results_subject_id'), 'results', ['subject_id'], unique=False)
    op.create_index(op.f('ix_results_quiz_id'), 'results', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_results_assignment_id'), 'results', ['assignment_id'], unique=False)
    
    # Create grading table
    op.create_table(
        'grading',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institute_id', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.Integer(), nullable=False),
        sa.Column('graded_by', sa.Integer(), nullable=True),
        sa.Column('grading_details', sa.Text(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['institute_id'], ['institutes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['result_id'], ['results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['graded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grading_id'), 'grading', ['id'], unique=False)
    op.create_index(op.f('ix_grading_institute_id'), 'grading', ['institute_id'], unique=False)
    op.create_index(op.f('ix_grading_result_id'), 'grading', ['result_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_grading_result_id'), table_name='grading')
    op.drop_index(op.f('ix_grading_institute_id'), table_name='grading')
    op.drop_index(op.f('ix_grading_id'), table_name='grading')
    op.drop_table('grading')
    
    op.drop_index(op.f('ix_results_assignment_id'), table_name='results')
    op.drop_index(op.f('ix_results_quiz_id'), table_name='results')
    op.drop_index(op.f('ix_results_subject_id'), table_name='results')
    op.drop_index(op.f('ix_results_class_id'), table_name='results')
    op.drop_index(op.f('ix_results_student_id'), table_name='results')
    op.drop_index(op.f('ix_results_institute_id'), table_name='results')
    op.drop_index(op.f('ix_results_id'), table_name='results')
    op.drop_table('results')
    
    op.drop_index(op.f('ix_assignment_submissions_student_id'), table_name='assignment_submissions')
    op.drop_index(op.f('ix_assignment_submissions_assignment_id'), table_name='assignment_submissions')
    op.drop_index(op.f('ix_assignment_submissions_id'), table_name='assignment_submissions')
    op.drop_table('assignment_submissions')
    
    op.drop_index(op.f('ix_assignments_created_by'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_subject_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_class_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_institute_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_id'), table_name='assignments')
    op.drop_table('assignments')
    
    op.drop_index(op.f('ix_quiz_attempt_answers_question_id'), table_name='quiz_attempt_answers')
    op.drop_index(op.f('ix_quiz_attempt_answers_attempt_id'), table_name='quiz_attempt_answers')
    op.drop_index(op.f('ix_quiz_attempt_answers_id'), table_name='quiz_attempt_answers')
    op.drop_table('quiz_attempt_answers')
    
    op.drop_index(op.f('ix_quiz_attempts_student_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_quiz_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_id'), table_name='quiz_attempts')
    op.drop_table('quiz_attempts')
    
    op.drop_index(op.f('ix_quiz_options_question_id'), table_name='quiz_options')
    op.drop_index(op.f('ix_quiz_options_id'), table_name='quiz_options')
    op.drop_table('quiz_options')
    
    op.drop_index(op.f('ix_quiz_questions_quiz_id'), table_name='quiz_questions')
    op.drop_index(op.f('ix_quiz_questions_id'), table_name='quiz_questions')
    op.drop_table('quiz_questions')
    
    op.drop_index(op.f('ix_quizzes_created_by'), table_name='quizzes')
    op.drop_index(op.f('ix_quizzes_subject_id'), table_name='quizzes')
    op.drop_index(op.f('ix_quizzes_class_id'), table_name='quizzes')
    op.drop_index(op.f('ix_quizzes_institute_id'), table_name='quizzes')
    op.drop_index(op.f('ix_quizzes_id'), table_name='quizzes')
    op.drop_table('quizzes')
