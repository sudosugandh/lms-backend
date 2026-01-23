from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class ResultType(str, enum.Enum):
    QUIZ = "QUIZ"
    ASSIGNMENT = "ASSIGNMENT"


class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Either quiz_id or assignment_id, but not both
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="SET NULL"), nullable=True)
    assignment_submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="SET NULL"), nullable=True)
    
    result_type = Column(String(20), nullable=False)  # QUIZ or ASSIGNMENT
    total_marks = Column(Integer, nullable=False)  # Total marks possible
    marks_obtained = Column(Integer, nullable=False)  # Marks obtained
    percentage = Column(Float, nullable=False)  # Percentage score
    grade = Column(String(10), nullable=True)  # Letter grade if applicable
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, GRADED, PUBLISHED
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    student = relationship("User", foreign_keys=[student_id])
    class_ = relationship("Class")
    subject = relationship("Subject")
    quiz = relationship("Quiz", back_populates="results")
    assignment = relationship("Assignment", back_populates="results")
    quiz_attempt = relationship("QuizAttempt", back_populates="result")
    assignment_submission = relationship("AssignmentSubmission", back_populates="result")
    
    # Ensure one result per quiz/assignment per student
    __table_args__ = (
        UniqueConstraint('student_id', 'quiz_id', name='uq_student_quiz_result'),
        UniqueConstraint('student_id', 'assignment_id', name='uq_student_assignment_result'),
    )


class Grading(Base):
    __tablename__ = "grading"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    result_id = Column(Integer, ForeignKey("results.id", ondelete="CASCADE"), nullable=False, index=True)
    graded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    grading_details = Column(Text, nullable=True)  # JSON or text details of grading breakdown
    feedback = Column(Text, nullable=True)  # Detailed feedback
    graded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    result = relationship("Result")
    grader = relationship("User", foreign_keys=[graded_by])
